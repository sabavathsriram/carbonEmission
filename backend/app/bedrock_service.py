import json
import re
import boto3
import logging
from typing import Optional
from .config import settings
from .models import ExtractedData, LineItem

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are an expert at extracting carbon emissions-related data from invoices and business documents.

Analyze the following text and extract all relevant information. Return a JSON object with these fields:
- vendor_name: string (supplier/vendor name)
- invoice_date: string (date in YYYY-MM-DD format if possible)
- invoice_number: string
- total_amount: number (total invoice amount)
- currency: string (e.g. USD, EUR, GBP)
- line_items: array of objects with fields: description, quantity, unit, amount, currency, category (limit to 5 most important items)
- energy_kwh: number (electricity consumption in kWh if present)
- fuel_liters: number (fuel volume in liters if present, convert gallons to liters if needed)
- fuel_type: string (diesel, petrol, natural_gas, etc.)
- distance_km: number (distance traveled in km if present, convert miles if needed)
- transport_mode: string (road, air, rail, sea)
- waste_kg: number (waste weight in kg if present)

For any field not found, use null. Be precise with numbers.

Document text:
{text}

Return ONLY valid JSON, no explanation. Keep line_items to 5 entries max."""


def summarize_csv(text: str, max_chars: int = 4000) -> str:
    """
    Summarize large CSV files by taking header + sample rows + totals.
    """
    lines = text.strip().split('\n')
    if len(lines) <= 20:
        return text[:max_chars]
    
    # Take header + first 10 rows + last 5 rows
    header = lines[0] if lines else ""
    sample_rows = lines[1:11]
    tail_rows = lines[-5:]
    
    summary = [header]
    summary.extend(sample_rows)
    summary.append("... [middle rows omitted] ...")
    summary.extend(tail_rows)
    
    result = '\n'.join(summary)
    return result[:max_chars]


def preprocess_text(text: str) -> str:
    """
    Preprocess input text for better extraction.
    For CSVs, summarize. For all text, limit size.
    """
    # Detect CSV
    if ',' in text[:200] and '\n' in text[:200]:
        lines = text.split('\n')
        if len(lines) > 20 and all(',' in line for line in lines[:5]):
            logger.info(f"Detected CSV with {len(lines)} lines, summarizing...")
            return summarize_csv(text, max_chars=4000)
    
    # Otherwise just truncate
    return text[:6000]


def extract_json_from_text(text: str) -> dict:
    """
    Extract JSON from text, handling markdown fences and truncation.
    """
    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
    
    text = text.strip()
    
    # Try parsing as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}, attempting repair...")
    
    # Attempt to repair truncated JSON
    # Find the last complete field before truncation
    try:
        # Remove trailing incomplete content
        text = re.sub(r',\s*$', '', text)  # trailing comma
        text = re.sub(r':\s*$', ': null', text)  # incomplete value
        text = re.sub(r':\s*"[^"]*$', ': null', text)  # incomplete string
        text = re.sub(r':\s*\[[^\]]*$', ': []', text)  # incomplete array
        
        # Ensure proper closing
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        text = text.rstrip(',')
        text += ']' * open_brackets
        text += '}' * open_braces
        
        return json.loads(text)
    except Exception as repair_error:
        logger.error(f"JSON repair failed: {repair_error}")
        # Return minimal valid JSON
        return {}


def get_bedrock_client():
    """Create and return a Bedrock runtime client."""
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.client("bedrock-runtime", **kwargs)


def extract_data_with_bedrock(text: str) -> tuple[ExtractedData, float]:
    """
    Use Amazon Bedrock (Claude) to extract structured data from text.
    Returns (ExtractedData, confidence_score).
    """
    try:
        client = get_bedrock_client()
        
        # Preprocess input (summarize CSVs, truncate long text)
        processed_text = preprocess_text(text)
        prompt = EXTRACTION_PROMPT.format(text=processed_text)

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,  # Increased for larger responses
            "temperature": 0.0,   # Deterministic for data extraction
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        response = client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())
        raw_output = response_body["content"][0]["text"].strip()

        # Extract and parse JSON with error handling
        extracted_json = extract_json_from_text(raw_output)

        # Build line items (limit to 10 to avoid bloat)
        line_items = []
        for item in extracted_json.get("line_items", [])[:10]:
            if isinstance(item, dict):
                line_items.append(LineItem(
                    description=item.get("description", ""),
                    quantity=item.get("quantity"),
                    unit=item.get("unit"),
                    amount=item.get("amount"),
                    currency=item.get("currency"),
                    category=item.get("category"),
                ))

        extracted = ExtractedData(
            vendor_name=extracted_json.get("vendor_name"),
            invoice_date=extracted_json.get("invoice_date"),
            invoice_number=extracted_json.get("invoice_number"),
            total_amount=extracted_json.get("total_amount"),
            currency=extracted_json.get("currency", "USD"),
            line_items=line_items,
            energy_kwh=extracted_json.get("energy_kwh"),
            fuel_liters=extracted_json.get("fuel_liters"),
            fuel_type=extracted_json.get("fuel_type"),
            distance_km=extracted_json.get("distance_km"),
            transport_mode=extracted_json.get("transport_mode"),
            waste_kg=extracted_json.get("waste_kg"),
            raw_text=text[:500],
        )

        # Confidence: higher if more fields populated
        populated = sum(1 for v in [
            extracted.vendor_name, extracted.invoice_date, extracted.energy_kwh,
            extracted.fuel_liters, extracted.distance_km, extracted.waste_kg
        ] if v is not None)
        confidence = min(0.95, 0.5 + (populated * 0.08))

        return extracted, confidence

    except Exception as e:
        logger.error(f"Bedrock extraction failed: {e}")
        # Return minimal extracted data with low confidence
        return ExtractedData(raw_text=text[:500]), 0.3
