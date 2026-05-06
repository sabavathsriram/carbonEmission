import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .models import (
    ProcessResponse, ReportRequest, ProcessInputRequest,
    UpdateExtractedDataRequest, ValidationResultModel, ValidationIssueModel,
    ESGData,
)
from .bedrock_service import extract_data_with_bedrock
from .emissions_calculator import calculate_emissions
from .report_generator import generate_pdf_report
from .file_processor import extract_text_from_file, SUPPORTED_EXTENSIONS
from .validation import validate_extracted_data, calculate_adjusted_confidence
from .esg_engine import (
    calculate_esg_score, run_what_if_simulations, generate_recommendations,
    generate_smart_alerts, generate_forecast, build_traceability,
)
from .auth import (
    UserCreate, UserLogin, TokenResponse, UserInfo,
    authenticate_user, register_user, create_access_token, get_current_user,
)
from .dynamodb import ensure_tables, save_emission_record, get_emission_history
from .notifications import (
    notify_welcome, notify_analysis_approved,
    notify_report_generated, notify_emission_spike,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Carbon Intelligence API",
    description="Enterprise GHG Emissions & ESG Intelligence Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    try:
        ensure_tables()
        logger.info("DynamoDB tables ready")
    except Exception as e:
        logger.warning(f"DynamoDB table setup failed (will use fallback): {e}")


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user["email"]})
    return TokenResponse(access_token=token, user_email=user["email"],
                         user_name=user["name"], role=user["role"])


@app.post("/api/auth/register", response_model=TokenResponse)
async def register(body: UserCreate):
    user = register_user(body.email, body.name, body.password)
    token = create_access_token({"sub": user["email"]})
    # Send welcome email + create SNS topic (non-blocking)
    try:
        notify_welcome(user["email"], user["name"])
    except Exception as e:
        logger.warning(f"Welcome notification failed: {e}")
    return TokenResponse(access_token=token, user_email=user["email"],
                         user_name=user["name"], role=user["role"])


@app.get("/api/auth/me", response_model=UserInfo)
async def me(current_user: UserInfo = Depends(get_current_user)):
    return current_user


# ── Emission history ──────────────────────────────────────────────────────────

@app.get("/api/emissions/history")
async def emission_history(current_user: UserInfo = Depends(get_current_user)):
    """Return the user's emission calculation history with trend comparison."""
    records = get_emission_history(current_user.email, limit=20)

    # Attach delta vs previous record
    for i, rec in enumerate(records):
        if i < len(records) - 1:
            prev = records[i + 1]
            delta = rec["total_kg_co2e"] - prev["total_kg_co2e"]
            rec["delta_kg"]  = round(delta, 3)
            rec["delta_pct"] = round((delta / prev["total_kg_co2e"] * 100) if prev["total_kg_co2e"] else 0, 1)
            rec["trend"]     = "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"
        else:
            rec["delta_kg"]  = None
            rec["delta_pct"] = None
            rec["trend"]     = "baseline"

    return {"records": records, "count": len(records)}


# ── Core helper ───────────────────────────────────────────────────────────────

def _build_process_response(text: str, source_msg: str, filename: str = "document") -> ProcessResponse:
    extracted, base_confidence = extract_data_with_bedrock(text)
    extracted.source_filename = filename
    validation = validate_extracted_data(extracted)
    final_confidence = calculate_adjusted_confidence(base_confidence, validation, extracted)
    extracted.raw_text = text[:500]

    emissions  = calculate_emissions(extracted, final_confidence)
    esg_raw    = calculate_esg_score(emissions, extracted)
    simulations    = run_what_if_simulations(extracted, emissions)
    recommendations = generate_recommendations(extracted, emissions)
    alerts     = generate_smart_alerts(extracted, emissions)
    forecast   = generate_forecast(emissions)
    traceability = build_traceability(extracted, filename)

    validation_model = ValidationResultModel(
        is_valid=validation.is_valid,
        requires_review=validation.requires_review,
        issues=[ValidationIssueModel(**i.to_dict()) for i in validation.issues],
        confidence_adjustment=validation.confidence_adjustment,
    )

    return ProcessResponse(
        extracted_data=extracted,
        emission_result=emissions,
        validation=validation_model,
        esg=ESGData(**esg_raw),
        simulations=simulations,
        recommendations=recommendations,
        alerts=alerts,
        forecast=forecast,
        traceability=traceability,
        success=True,
        message=source_msg,
    )


# ── Process endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Carbon Intelligence API v2"}


@app.post("/api/process/text", response_model=ProcessResponse)
async def process_text(
    request: ProcessInputRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    if not request.text_input or not request.text_input.strip():
        raise HTTPException(status_code=400, detail="text_input is required")
    text = request.text_input.strip()
    logger.info(f"[{current_user.email}] Processing text ({len(text)} chars)")
    return _build_process_response(text, "Text processed successfully", "manual input")


@app.post("/api/process/file", response_model=ProcessResponse)
async def process_file(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    filename = file.filename or ""
    if not any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_bytes = await file.read()
    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 20 MB)")

    logger.info(f"[{current_user.email}] Processing file: {filename} ({len(file_bytes)} bytes)")
    text = extract_text_from_file(file_bytes, filename)
    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the uploaded file.")

    return _build_process_response(text, f"File '{filename}' processed successfully", filename)


@app.post("/api/process/revalidate", response_model=ProcessResponse)
async def revalidate(
    request: UpdateExtractedDataRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    extracted = request.extracted_data
    validation = validate_extracted_data(extracted)
    base_confidence = 0.75 if request.approved else 0.65
    final_confidence = calculate_adjusted_confidence(base_confidence, validation, extracted)
    emissions = calculate_emissions(extracted, final_confidence)

    esg_raw = calculate_esg_score(emissions, extracted)
    simulations = run_what_if_simulations(extracted, emissions)
    recommendations = generate_recommendations(extracted, emissions)
    alerts = generate_smart_alerts(extracted, emissions)
    forecast = generate_forecast(emissions)
    traceability = build_traceability(extracted, extracted.source_filename or "document")

    # Save to DynamoDB and send notifications when user approves
    if request.approved and validation.is_valid:
        record_id = save_emission_record(
            user_email=current_user.email,
            source_filename=extracted.source_filename or "document",
            total_kg=emissions.total_kg_co2e,
            scope1_kg=emissions.scope1_kg_co2e,
            scope2_kg=emissions.scope2_kg_co2e,
            scope3_kg=emissions.scope3_kg_co2e,
            confidence=emissions.confidence_score,
            esg_score=esg_raw.get("score"),
        )

        # Compute delta vs previous record for notification
        history = get_emission_history(current_user.email, limit=2)
        delta_pct: Optional[float] = None
        if len(history) >= 2:
            prev_total = history[1]["total_kg_co2e"]
            if prev_total > 0:
                delta_pct = round(
                    (emissions.total_kg_co2e - prev_total) / prev_total * 100, 1
                )

        # Send approval summary email
        try:
            notify_analysis_approved(
                email=current_user.email,
                user_name=current_user.name,
                source_filename=extracted.source_filename or "document",
                total_kg=emissions.total_kg_co2e,
                scope1_kg=emissions.scope1_kg_co2e,
                scope2_kg=emissions.scope2_kg_co2e,
                scope3_kg=emissions.scope3_kg_co2e,
                esg_score=esg_raw.get("score", 0),
                confidence=emissions.confidence_score,
                delta_pct=delta_pct,
            )
        except Exception as e:
            logger.warning(f"Approval notification failed: {e}")

        # Send spike alert if emissions increased >20%
        if delta_pct is not None and delta_pct > 20 and len(history) >= 2:
            try:
                notify_emission_spike(
                    email=current_user.email,
                    user_name=current_user.name,
                    source_filename=extracted.source_filename or "document",
                    total_kg=emissions.total_kg_co2e,
                    prev_total_kg=history[1]["total_kg_co2e"],
                    delta_pct=delta_pct,
                )
            except Exception as e:
                logger.warning(f"Spike notification failed: {e}")

    validation_model = ValidationResultModel(
        is_valid=validation.is_valid,
        requires_review=validation.requires_review and not request.approved,
        issues=[ValidationIssueModel(**i.to_dict()) for i in validation.issues],
        confidence_adjustment=validation.confidence_adjustment,
    )

    return ProcessResponse(
        extracted_data=extracted,
        emission_result=emissions,
        validation=validation_model,
        esg=ESGData(**esg_raw),
        simulations=simulations,
        recommendations=recommendations,
        alerts=alerts,
        forecast=forecast,
        traceability=traceability,
        success=True,
        message="Approved & saved to history" if request.approved else "Data updated",
    )


@app.post("/api/report/generate")
async def generate_report(
    request: ReportRequest,
    current_user: UserInfo = Depends(get_current_user),
):
    try:
        pdf_bytes = generate_pdf_report(
            company=request.company_details,
            extracted=request.extracted_data,
            emissions=request.emission_result,
            esg_data=request.esg_data,
            recommendations=request.recommendations or [],
            forecast=request.forecast,
        )
        slug = request.company_details.company_name.replace(" ", "_").lower()

        # Send report-generated notification
        try:
            notify_report_generated(
                email=current_user.email,
                user_name=current_user.name,
                company_name=request.company_details.company_name,
                reporting_period=request.company_details.reporting_period,
                total_kg=request.emission_result.total_kg_co2e,
                esg_score=request.esg_data.get("score") if request.esg_data else None,
            )
        except Exception as e:
            logger.warning(f"Report notification failed: {e}")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="carbon_report_{slug}.pdf"'},
        )
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
