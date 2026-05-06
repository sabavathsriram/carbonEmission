import axios from 'axios';
import type { ProcessResponse, CompanyDetails, ExtractedData, EmissionResult, AuthUser, EmissionRecord } from './types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use(config => {
  try {
    const stored = localStorage.getItem('ci_user');
    if (stored) {
      const user: AuthUser = JSON.parse(stored);
      if (user.token) config.headers['Authorization'] = `Bearer ${user.token}`;
    }
  } catch {}
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────
export async function loginUser(email: string, password: string): Promise<AuthUser> {
  const { data } = await api.post('/api/auth/login', { email, password });
  return { email: data.user_email, name: data.user_name, role: data.role, token: data.access_token };
}

export async function registerUser(email: string, name: string, password: string): Promise<AuthUser> {
  const { data } = await api.post('/api/auth/register', { email, name, password });
  return { email: data.user_email, name: data.user_name, role: data.role, token: data.access_token };
}

// ── Process ───────────────────────────────────────────────────────────────
export async function processText(text: string): Promise<ProcessResponse> {
  const { data } = await api.post<ProcessResponse>('/api/process/text', { text_input: text });
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

export async function revalidateData(extractedData: ExtractedData, approved: boolean): Promise<ProcessResponse> {
  const { data } = await api.post<ProcessResponse>('/api/process/revalidate', {
    extracted_data: extractedData, approved,
  });
  return data;
}

// ── History ───────────────────────────────────────────────────────────────
export async function getEmissionHistory(): Promise<{ records: EmissionRecord[]; count: number }> {
  const { data } = await api.get('/api/emissions/history');
  return data;
}

// ── Report ────────────────────────────────────────────────────────────────
export async function generateReport(
  companyDetails: CompanyDetails,
  extractedData: ExtractedData,
  emissionResult: EmissionResult,
  esgData?: object,
  recommendations?: object[],
  forecast?: object,
): Promise<Blob> {
  const response = await api.post(
    '/api/report/generate',
    { company_details: companyDetails, extracted_data: extractedData,
      emission_result: emissionResult, esg_data: esgData,
      recommendations, forecast },
    { responseType: 'blob' }
  );
  return response.data;
}
