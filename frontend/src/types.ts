export interface LineItem {
  description: string; quantity?: number; unit?: string;
  amount?: number; currency?: string; category?: string;
}
export interface ExtractedData {
  vendor_name?: string; invoice_date?: string; invoice_number?: string;
  total_amount?: number; currency?: string; line_items: LineItem[];
  energy_kwh?: number; fuel_liters?: number; fuel_type?: string;
  distance_km?: number; transport_mode?: string; waste_kg?: number;
  raw_text?: string; source_filename?: string;
}
export interface BreakdownItem {
  category: string; quantity: number; unit: string;
  emission_factor: number; kg_co2e: number;
  fuel_type?: string; transport_mode?: string; note?: string;
}
export interface EmissionResult {
  scope1_kg_co2e: number; scope2_kg_co2e: number; scope3_kg_co2e: number;
  total_kg_co2e: number; breakdown: BreakdownItem[];
  confidence_score: number; methodology_notes: string;
}
export type ValidationSeverity = 'error' | 'warning' | 'info';
export interface ValidationIssue {
  field: string; severity: ValidationSeverity; message: string;
  current_value?: number; suggested_value?: number;
}
export interface ValidationResult {
  is_valid: boolean; requires_review: boolean;
  issues: ValidationIssue[]; confidence_adjustment: number;
}
export interface ESGData {
  score: number; grade: string; label: string; color: string;
  breakdown: { data_completeness: number; confidence: number; emission_intensity: string; scope1_ratio: number; };
}
export interface SimulationResult {
  id: string; title: string; description: string; category: string;
  operational_note: string; reduction_pct: number;
  emission_reduction_kg: number; emission_reduction_tonnes: number;
  new_total_kg: number; cost_saving_usd: number;
  esg_score_improvement: number; scope: string;
}
export interface Recommendation {
  id: string; priority: 'high' | 'medium' | 'low'; category: string;
  title: string; insight: string; action: string; impact: string;
  maintains_output: boolean; revenue_impact?: string;
}
export interface SmartAlert {
  type: string; severity: 'high' | 'medium' | 'low'; icon: string;
  title: string; message: string;
}
export interface ForecastMonth { month: string; bau: number; optimized: number; target: number; }
export interface Forecast {
  monthly_data: ForecastMonth[];
  yearly_summary: {
    bau_total_kg: number; optimized_total_kg: number; target_total_kg: number;
    bau_total_tonnes: number; optimized_saving_kg: number; target_saving_kg: number;
  };
  trajectory: string;
}
export interface TraceabilityItem {
  field: string; value: string; source: string;
  extraction_method: string; confidence: string;
}
export interface ProcessResponse {
  extracted_data: ExtractedData; emission_result: EmissionResult;
  validation: ValidationResult; esg?: ESGData;
  simulations?: SimulationResult[]; recommendations?: Recommendation[];
  alerts?: SmartAlert[]; forecast?: Forecast;
  traceability?: TraceabilityItem[];
  success: boolean; message: string;
}
export interface CompanyDetails {
  company_name: string; industry: string; reporting_period: string;
  contact_name?: string; contact_email?: string; additional_notes?: string;
}
export type WorkflowStage = 'login' | 'input' | 'extracting' | 'review' | 'approved' | 'report';
export interface AuthUser { email: string; name: string; role: string; token: string; }

export interface EmissionRecord {
  user_email: string;
  record_id: string;
  timestamp: string;
  source_filename: string;
  total_kg_co2e: number;
  scope1_kg_co2e: number;
  scope2_kg_co2e: number;
  scope3_kg_co2e: number;
  confidence_score: number;
  esg_score: number;
  delta_kg?: number | null;
  delta_pct?: number | null;
  trend?: string;
}
