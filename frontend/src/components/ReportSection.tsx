import React, { useState } from 'react';
import { FileDown, Building2, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { generateReport } from '../api';
import { CompanyDetails, ExtractedData, EmissionResult } from '../types';

interface Props {
  extractedData: ExtractedData;
  emissionResult: EmissionResult;
}

const INDUSTRIES = [
  'Manufacturing', 'Retail', 'Technology', 'Healthcare', 'Finance',
  'Transportation & Logistics', 'Energy & Utilities', 'Construction',
  'Agriculture', 'Hospitality', 'Education', 'Other',
];

export default function ReportSection({ extractedData, emissionResult }: Props) {
  const [company, setCompany] = useState<CompanyDetails>({
    company_name: '',
    industry: '',
    reporting_period: '',
    contact_name: '',
    contact_email: '',
    additional_notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const update = (field: keyof CompanyDetails, value: string) =>
    setCompany((prev) => ({ ...prev, [field]: value }));

  const handleGenerate = async () => {
    if (!company.company_name || !company.industry || !company.reporting_period) {
      setStatus('error');
      setErrorMsg('Please fill in Company Name, Industry, and Reporting Period.');
      return;
    }
    setLoading(true);
    setStatus('idle');
    setErrorMsg('');
    try {
      const blob = await generateReport(company, extractedData, emissionResult);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `carbon_report_${company.company_name.replace(/\s+/g, '_').toLowerCase()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setStatus('success');
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Report generation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="section-title">
        <Building2 size={20} />
        Generate Report
      </h2>

      <div className="form-grid">
        <div className="form-group required">
          <label>Company Name</label>
          <input
            type="text"
            placeholder="Acme Corporation"
            value={company.company_name}
            onChange={(e) => update('company_name', e.target.value)}
          />
        </div>

        <div className="form-group required">
          <label>Industry</label>
          <select value={company.industry} onChange={(e) => update('industry', e.target.value)}>
            <option value="">Select industry...</option>
            {INDUSTRIES.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>

        <div className="form-group required">
          <label>Reporting Period</label>
          <input
            type="text"
            placeholder="e.g. Q1 2024 or Jan–Mar 2024"
            value={company.reporting_period}
            onChange={(e) => update('reporting_period', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Contact Name</label>
          <input
            type="text"
            placeholder="Jane Smith"
            value={company.contact_name}
            onChange={(e) => update('contact_name', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Contact Email</label>
          <input
            type="email"
            placeholder="jane@company.com"
            value={company.contact_email}
            onChange={(e) => update('contact_email', e.target.value)}
          />
        </div>

        <div className="form-group full-width">
          <label>Additional Notes</label>
          <textarea
            placeholder="Any additional context for the report..."
            value={company.additional_notes}
            onChange={(e) => update('additional_notes', e.target.value)}
            rows={3}
          />
        </div>
      </div>

      {status === 'error' && (
        <div className="error-banner">
          <AlertCircle size={16} /> {errorMsg}
        </div>
      )}
      {status === 'success' && (
        <div className="success-banner">
          <CheckCircle size={16} /> Report downloaded successfully!
        </div>
      )}

      <button className="btn-primary" onClick={handleGenerate} disabled={loading}>
        {loading ? (
          <><Loader2 size={18} className="spin" /> Generating PDF...</>
        ) : (
          <><FileDown size={18} /> Download PDF Report</>
        )}
      </button>
    </div>
  );
}
