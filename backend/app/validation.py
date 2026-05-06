"""
Enterprise-grade validation and anomaly detection for extracted data.
"""
from typing import List, Dict, Any
from enum import Enum
from .models import ExtractedData, EmissionResult


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue:
    def __init__(
        self,
        field: str,
        severity: ValidationSeverity,
        message: str,
        current_value: Any = None,
        suggested_value: Any = None,
    ):
        self.field = field
        self.severity = severity
        self.message = message
        self.current_value = current_value
        self.suggested_value = suggested_value

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "severity": self.severity,
            "message": self.message,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
        }


class ValidationResult:
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.is_valid: bool = True
        self.requires_review: bool = False
        self.confidence_adjustment: float = 0.0

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.is_valid = False
            self.confidence_adjustment -= 0.15
        elif issue.severity == ValidationSeverity.WARNING:
            self.requires_review = True
            self.confidence_adjustment -= 0.08

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "requires_review": self.requires_review,
            "issues": [issue.to_dict() for issue in self.issues],
            "confidence_adjustment": self.confidence_adjustment,
        }


# Anomaly thresholds
THRESHOLDS = {
    "energy_kwh_max": 1_000_000,  # 1M kWh per invoice is unusual
    "energy_kwh_high": 100_000,   # 100k kWh warrants review
    "fuel_liters_max": 100_000,   # 100k liters is extreme
    "fuel_liters_high": 10_000,   # 10k liters warrants review
    "distance_km_max": 100_000,   # 100k km is extreme
    "distance_km_high": 10_000,   # 10k km warrants review
    "waste_kg_max": 100_000,      # 100 tonnes is extreme
    "waste_kg_high": 10_000,      # 10 tonnes warrants review
    "total_amount_max": 10_000_000,  # $10M invoice is extreme
    "total_amount_high": 1_000_000,  # $1M warrants review
}


def validate_extracted_data(data: ExtractedData) -> ValidationResult:
    """
    Validate extracted data for missing values, negative values, and anomalies.
    """
    result = ValidationResult()

    # --- Missing Critical Fields ---
    if not data.vendor_name:
        result.add_issue(ValidationIssue(
            field="vendor_name",
            severity=ValidationSeverity.WARNING,
            message="Vendor name missing - manual entry recommended",
        ))

    if not data.invoice_date:
        result.add_issue(ValidationIssue(
            field="invoice_date",
            severity=ValidationSeverity.WARNING,
            message="Invoice date missing - reporting accuracy may be affected",
        ))

    if not data.invoice_number:
        result.add_issue(ValidationIssue(
            field="invoice_number",
            severity=ValidationSeverity.INFO,
            message="Invoice number missing - tracking may be difficult",
        ))

    # --- Missing Emissions Data ---
    emissions_fields = [
        data.energy_kwh,
        data.fuel_liters,
        data.distance_km,
        data.waste_kg,
    ]
    if all(v is None for v in emissions_fields):
        result.add_issue(ValidationIssue(
            field="emissions_data",
            severity=ValidationSeverity.ERROR,
            message="No emissions-related data found - cannot calculate carbon footprint accurately",
        ))
        result.add_issue(ValidationIssue(
            field="emissions_data",
            severity=ValidationSeverity.WARNING,
            message="Falling back to spend-based estimation (low accuracy)",
        ))

    # --- Negative Value Validation ---
    if data.energy_kwh is not None and data.energy_kwh < 0:
        result.add_issue(ValidationIssue(
            field="energy_kwh",
            severity=ValidationSeverity.ERROR,
            message="Electricity consumption cannot be negative",
            current_value=data.energy_kwh,
            suggested_value=0,
        ))

    if data.fuel_liters is not None and data.fuel_liters < 0:
        result.add_issue(ValidationIssue(
            field="fuel_liters",
            severity=ValidationSeverity.ERROR,
            message="Fuel volume cannot be negative",
            current_value=data.fuel_liters,
            suggested_value=0,
        ))

    if data.distance_km is not None and data.distance_km < 0:
        result.add_issue(ValidationIssue(
            field="distance_km",
            severity=ValidationSeverity.ERROR,
            message="Distance traveled cannot be negative",
            current_value=data.distance_km,
            suggested_value=0,
        ))

    if data.waste_kg is not None and data.waste_kg < 0:
        result.add_issue(ValidationIssue(
            field="waste_kg",
            severity=ValidationSeverity.ERROR,
            message="Waste weight cannot be negative",
            current_value=data.waste_kg,
            suggested_value=0,
        ))

    if data.total_amount is not None and data.total_amount < 0:
        result.add_issue(ValidationIssue(
            field="total_amount",
            severity=ValidationSeverity.ERROR,
            message="Invoice amount cannot be negative",
            current_value=data.total_amount,
            suggested_value=0,
        ))

    # --- Anomaly Detection: Extremely High Values ---
    if data.energy_kwh is not None:
        if data.energy_kwh > THRESHOLDS["energy_kwh_max"]:
            result.add_issue(ValidationIssue(
                field="energy_kwh",
                severity=ValidationSeverity.ERROR,
                message=f"Electricity usage extremely high ({data.energy_kwh:,.0f} kWh) - likely extraction error",
                current_value=data.energy_kwh,
            ))
        elif data.energy_kwh > THRESHOLDS["energy_kwh_high"]:
            result.add_issue(ValidationIssue(
                field="energy_kwh",
                severity=ValidationSeverity.WARNING,
                message=f"Unusually high electricity usage ({data.energy_kwh:,.0f} kWh) - please verify",
                current_value=data.energy_kwh,
            ))

    if data.fuel_liters is not None:
        if data.fuel_liters > THRESHOLDS["fuel_liters_max"]:
            result.add_issue(ValidationIssue(
                field="fuel_liters",
                severity=ValidationSeverity.ERROR,
                message=f"Fuel volume extremely high ({data.fuel_liters:,.0f} L) - likely extraction error",
                current_value=data.fuel_liters,
            ))
        elif data.fuel_liters > THRESHOLDS["fuel_liters_high"]:
            result.add_issue(ValidationIssue(
                field="fuel_liters",
                severity=ValidationSeverity.WARNING,
                message=f"Unusually high fuel volume ({data.fuel_liters:,.0f} L) - please verify",
                current_value=data.fuel_liters,
            ))

    if data.distance_km is not None:
        if data.distance_km > THRESHOLDS["distance_km_max"]:
            result.add_issue(ValidationIssue(
                field="distance_km",
                severity=ValidationSeverity.ERROR,
                message=f"Travel distance extremely high ({data.distance_km:,.0f} km) - likely extraction error",
                current_value=data.distance_km,
            ))
        elif data.distance_km > THRESHOLDS["distance_km_high"]:
            result.add_issue(ValidationIssue(
                field="distance_km",
                severity=ValidationSeverity.WARNING,
                message=f"Unusually high travel distance ({data.distance_km:,.0f} km) - please verify",
                current_value=data.distance_km,
            ))

    if data.waste_kg is not None:
        if data.waste_kg > THRESHOLDS["waste_kg_max"]:
            result.add_issue(ValidationIssue(
                field="waste_kg",
                severity=ValidationSeverity.ERROR,
                message=f"Waste weight extremely high ({data.waste_kg:,.0f} kg) - likely extraction error",
                current_value=data.waste_kg,
            ))
        elif data.waste_kg > THRESHOLDS["waste_kg_high"]:
            result.add_issue(ValidationIssue(
                field="waste_kg",
                severity=ValidationSeverity.WARNING,
                message=f"Unusually high waste weight ({data.waste_kg:,.0f} kg) - please verify",
                current_value=data.waste_kg,
            ))

    if data.total_amount is not None:
        if data.total_amount > THRESHOLDS["total_amount_max"]:
            result.add_issue(ValidationIssue(
                field="total_amount",
                severity=ValidationSeverity.ERROR,
                message=f"Invoice amount extremely high ({data.currency or '$'}{data.total_amount:,.2f}) - likely extraction error",
                current_value=data.total_amount,
            ))
        elif data.total_amount > THRESHOLDS["total_amount_high"]:
            result.add_issue(ValidationIssue(
                field="total_amount",
                severity=ValidationSeverity.WARNING,
                message=f"Unusually high invoice amount ({data.currency or '$'}{data.total_amount:,.2f}) - please verify",
                current_value=data.total_amount,
            ))

    # --- Missing Units/Types ---
    if data.fuel_liters is not None and data.fuel_liters > 0 and not data.fuel_type:
        result.add_issue(ValidationIssue(
            field="fuel_type",
            severity=ValidationSeverity.WARNING,
            message="Fuel type missing - defaulting to diesel for calculation",
        ))

    if data.distance_km is not None and data.distance_km > 0 and not data.transport_mode:
        result.add_issue(ValidationIssue(
            field="transport_mode",
            severity=ValidationSeverity.WARNING,
            message="Transport mode missing - defaulting to road freight for calculation",
        ))

    return result


def calculate_adjusted_confidence(
    base_confidence: float,
    validation_result: ValidationResult,
    extracted_data: ExtractedData,
) -> float:
    """
    Calculate final confidence score with validation adjustments.
    """
    confidence = base_confidence + validation_result.confidence_adjustment

    # Boost confidence if key fields are present
    if extracted_data.vendor_name:
        confidence += 0.05
    if extracted_data.invoice_date:
        confidence += 0.05
    if extracted_data.invoice_number:
        confidence += 0.03

    # Boost if units/types are specified
    if extracted_data.fuel_type:
        confidence += 0.03
    if extracted_data.transport_mode:
        confidence += 0.03

    # Cap between 0 and 1
    return max(0.0, min(1.0, confidence))
