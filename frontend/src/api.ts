import axios from 'axios';
import type { ProcessResponse, CompanyDetails, ExtractedData, EmissionResult } from './types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

export async function processText(text: string): Promise<ProcessResponse> {
  const { data } = await api.post<ProcessResponse>('/api/process/text', {
    text_input: text,
  });
  return data;
}

export async function processFile(file: File): Promise<ProcessResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<ProcessResponse>('/api/process/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function generateReport(
  companyDetails: CompanyDetails,
  extractedData: ExtractedData,
  emissionResult: EmissionResult
): Promise<Blob> {
  const response = await api.post(
    '/api/report/generate',
    { company_details: companyDetails, extracted_data: extractedData, emission_result: emissionResult },
    { responseType: 'blob' }
  );
  return response.data;
}
