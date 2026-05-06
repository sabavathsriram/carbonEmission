import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import json

from .models import (
    ProcessResponse, ReportRequest, CompanyDetails,
    ExtractedData, EmissionResult, ProcessInputRequest
)
from .bedrock_service import extract_data_with_bedrock
from .emissions_calculator import calculate_emissions
from .report_generator import generate_pdf_report
from .file_processor import extract_text_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Carbon Intelligence API",
    description="GHG emissions extraction and reporting API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Carbon Intelligence API"}


@app.post("/api/process/text", response_model=ProcessResponse)
async def process_text(request: ProcessInputRequest):
    """Process plain text input to extract emissions data."""
    if not request.text_input or not request.text_input.strip():
        raise HTTPException(status_code=400, detail="text_input is required")

    text = request.text_input.strip()
    logger.info(f"Processing text input ({len(text)} chars)")

    extracted, confidence = extract_data_with_bedrock(text)
    emissions = calculate_emissions(extracted, confidence)

    return ProcessResponse(
        extracted_data=extracted,
        emission_result=emissions,
        success=True,
        message="Text processed successfully",
    )


@app.post("/api/process/file", response_model=ProcessResponse)
async def process_file(file: UploadFile = File(...)):
    """Process uploaded file (PDF or text) to extract emissions data."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_types = {
        "application/pdf", "text/plain", "text/csv",
        "application/octet-stream",
    }
    content_type = file.content_type or ""
    filename = file.filename or ""

    if not (
        content_type in allowed_types
        or filename.lower().endswith((".pdf", ".txt", ".csv"))
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF or text files."
        )

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    logger.info(f"Processing file: {filename} ({len(file_bytes)} bytes)")

    text = extract_text_from_file(file_bytes, filename)
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the uploaded file."
        )

    extracted, confidence = extract_data_with_bedrock(text)
    emissions = calculate_emissions(extracted, confidence)

    return ProcessResponse(
        extracted_data=extracted,
        emission_result=emissions,
        success=True,
        message=f"File '{filename}' processed successfully",
    )


@app.post("/api/report/generate")
async def generate_report(request: ReportRequest):
    """Generate a PDF emissions report."""
    try:
        pdf_bytes = generate_pdf_report(
            company=request.company_details,
            extracted=request.extracted_data,
            emissions=request.emission_result,
        )
        company_slug = request.company_details.company_name.replace(" ", "_").lower()
        filename = f"carbon_report_{company_slug}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
