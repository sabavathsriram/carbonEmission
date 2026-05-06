import json
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
- line_items: array of objects with fields: description, quantity, unit, amount, currency, category
- energy_kwh: number (electricity consumption in kWh if present)
- fuel_liters: number (fuel volume in liters if present, convert gallons to liters if needed)
- fuel_type: string (diesel, petrol, natural_gas, etc.)
- distance_km: number (distance traveled in km if present, convert miles if needed)
- transport_mode: string (road, air, rail, sea)
- waste_kg: number (waste weight in kg if present)

For any field not found, use null. Be precise with numbers.

Document text:
{text}

Return ONLY valid JSON, no explanation."""


def get_bedrock_client():
    """Create and return a Bedrock runtime client."""
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("bedrock-runtime", **kwargs)


def extract_data_with_bedrock(text: str) -> tuple[ExtractedData, float]:
    """
    Use Amazon Bedrock (Claude) to extract structured data from text.
    Returns (ExtractedData, confidence_score).
    """
    try:
        client = get_bedrock_client()
        prompt = EXTRACTION_PROMPT.format(text=text[:8000])  # limit input size

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
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

        # Strip markdown code fences if present
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]

        extracted_json = json.loads(raw_output)

        # Build line items
        line_items = []
        for item in extracted_json.get("line_items", []):
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
