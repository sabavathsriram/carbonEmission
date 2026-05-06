from pydantic import BaseModel
from typing import Optional, List, Any
from enum import Enum


class EmissionCategory(str, Enum):
    SCOPE1 = "scope1"
    SCOPE2 = "scope2"
    SCOPE3 = "scope3"


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None


class ExtractedData(BaseModel):
    vendor_name: Optional[str] = None
    invoice_date: Optional[str] = None
    invoice_number: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    line_items: List[LineItem] = []
    energy_kwh: Optional[float] = None
    fuel_liters: Optional[float] = None
    fuel_type: Optional[str] = None
    distance_km: Optional[float] = None
    transport_mode: Optional[str] = None
    waste_kg: Optional[float] = None
    raw_text: Optional[str] = None
    source_filename: Optional[str] = None


class EmissionResult(BaseModel):
    scope1_kg_co2e: float = 0.0
    scope2_kg_co2e: float = 0.0
    scope3_kg_co2e: float = 0.0
    total_kg_co2e: float = 0.0
    breakdown: List[dict] = []
    confidence_score: float = 0.0
    methodology_notes: str = ""


class CompanyDetails(BaseModel):
    company_name: str
    industry: str
    reporting_period: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    additional_notes: Optional[str] = None


class ProcessInputRequest(BaseModel):
    text_input: Optional[str] = None


class ReportRequest(BaseModel):
    company_details: CompanyDetails
    extracted_data: ExtractedData
    emission_result: EmissionResult
    esg_data: Optional[dict] = None
    recommendations: Optional[List[dict]] = None
    forecast: Optional[dict] = None


class ValidationIssueModel(BaseModel):
    field: str
    severity: str
    message: str
    current_value: Optional[float] = None
    suggested_value: Optional[float] = None


class ValidationResultModel(BaseModel):
    is_valid: bool
    requires_review: bool
    issues: List[ValidationIssueModel]
    confidence_adjustment: float


class ESGData(BaseModel):
    score: float
    grade: str
    label: str
    color: str
    breakdown: dict


class ProcessResponse(BaseModel):
    extracted_data: ExtractedData
    emission_result: EmissionResult
    validation: ValidationResultModel
    esg: Optional[ESGData] = None
    simulations: Optional[List[dict]] = None
    recommendations: Optional[List[dict]] = None
    alerts: Optional[List[dict]] = None
    forecast: Optional[dict] = None
    traceability: Optional[List[dict]] = None
    success: bool = True
    message: str = ""


class UpdateExtractedDataRequest(BaseModel):
    extracted_data: ExtractedData
    approved: bool = False
