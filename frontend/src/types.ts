export interface LineItem {
  description: string;
  quantity?: number;
  unit?: string;
  amount?: number;
  currency?: string;
  category?: string;
}

export interface ExtractedData {
  vendor_name?: string;
  invoice_date?: string;
  invoice_number?: string;
  total_amount?: number;
  currency?: string;
  line_items: LineItem[];
  energy_kwh?: number;
  fuel_liters?: number;
  fuel_type?: string;
  distance_km?: number;
  transport_mode?: string;
  waste_kg?: number;
  raw_text?: string;
}

export interface BreakdownItem {
  category: string;
  quantity: number;
  unit: string;
  emission_factor: number;
  kg_co2e: number;
  fuel_type?: string;
  transport_mode?: string;
  note?: string;
}

export interface EmissionResult {
  scope1_kg_co2e: number;
  scope2_kg_co2e: number;
  scope3_kg_co2e: number;
  total_kg_co2e: number;
  breakdown: BreakdownItem[];
  confidence_score: number;
  methodology_notes: string;
}

export interface ProcessResponse {
  extracted_data: ExtractedData;
  emission_result: EmissionResult;
  success: boolean;
  message: string;
}

export interface CompanyDetails {
  company_name: string;
  industry: string;
  reporting_period: string;
  contact_name?: string;
  contact_email?: string;
  additional_notes?: string;
}
