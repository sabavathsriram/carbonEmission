import React, { useState, useEffect } from 'react';
import { FileDown, Building2, Loader2, CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import { generateReport } from '../api';
import type { CompanyDetails, ExtractedData, EmissionResult, ESGData, Recommendation, Forecast } from '../types';

interface Props {
  extractedData: ExtractedData;
  emissionResult: EmissionResult;
  esgData?: ESGData;
  recommendations?: Recommendation[];
  forecast?: Forecast;
}

const INDUSTRIES = [
  'Manufacturing', 'Retail', 'Technology', 'Healthcare', 'Finance',
  'Transportation & Logistics', 'Energy & Utilities', 'Construction',
  'Agriculture', 'Hospitality', 'Education', 'Other',
];

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export default function ReportSection({ extractedData, emissionResult, esgData, recommendations, forecast }: Props) {
  const [company, setCompany] = useState<CompanyDetails>({
    company_name: '',
    industry: '',
    reporting_period: '',
    contact_name: '',
    contact_email: '',
    additional_notes: '',
  });
  const [autoFilled, setAutoFilled] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  // Auto-fill from extracted data on mount
  useEffect(() => {
    const filled = new Set<string>();
    const updates: Partial<CompanyDetails> = {};

    if (extractedData.vendor_name) {
      updates.company_name = extractedData.vendor_name;
      filled.add('company_name');
    }
    if (extractedData.invoice_date) {
      // Use invoice date as reporting period hint
      const date = new Date(extractedData.invoice_date);
      if (!isNaN(date.getTime())) {
        const month = date.toLocaleString('default', { month: 'long' });
        const year = date.getFullYear();
        updates.reporting_period = `${month} ${year}`;
        filled.add('reporting_period');
      }
    }

    if (Object.keys(updates).length > 0) {
      setCompany(prev => ({ ...prev, ...updates }));
      setAutoFilled(filled);
    }
  }, [extractedData]);

  const update = (field: keyof CompanyDetails, value: string) =>
    setCompany(prev => ({ ...prev, [field]: value }));

  // Determine which fields are missing
  const requiredFields: Array<{ key: keyof CompanyDetails; label: string }> = [
    { key: 'company_name', label: 'Company Name' },
    { key: 'industry', label: 'Industry' },
    { key: 'reporting_period', label: 'Reporting Period' },
  ];

  const missingRequired = requiredFields.filter(f => !company[f.key]);
  const allRequiredFilled = missingRequired.length === 0;

  // Optional fields that are missing
  const optionalMissing = [
    { key: 'contact_name' as keyof CompanyDetails, label: 'Contact Name' },
    { key: 'contact_email' as keyof CompanyDetails, label: 'Contact Email' },
  ].filter(f => !company[f.key]);

  const allFieldsFilled = allRequiredFilled && optionalMissing.length === 0;

  const handleGenerate = async () => {
    if (!allRequiredFilled) {
      setStatus('error');
      setErrorMsg(`Please fill in: ${missingRequired.map(f => f.label).join(', ')}`);
      return;
    }
    if (company.contact_email && !isValidEmail(company.contact_email)) {
      setStatus('error');
      setErrorMsg('Please enter a valid email address.');
      return;
    }
    setLoading(true);
    setStatus('idle');
    setErrorMsg('');
    try {
      const blob = await generateReport(company, extractedData, emissionResult, esgData, recommendations, forecast);
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

      {/* Auto-fill notice */}
      {autoFilled.size > 0 && (
        <div className="autofill-notice">
          <Sparkles size={14} />
          <span>
            {autoFilled.size} field{autoFilled.size > 1 ? 's' : ''} auto-filled from document
            ({Array.from(autoFilled).map(f => f.replace('_', ' ')).join(', ')})
          </span>
        </div>
      )}

      {/* All fields detected */}
      {allFieldsFilled && (
        <div className="success-banner" style={{ marginBottom: 16 }}>
          <CheckCircle size={15} />
          All report details detected successfully — ready to generate
        </div>
      )}

      {/* Only show fields that are missing or need input */}
      <div className="form-grid">
        {/* Company Name — always show */}
        <div className={`form-group required ${autoFilled.has('company_name') ? 'autofilled' : ''}`}>
          <label>
            Company Name
            {autoFilled.has('company_name') && <span className="autofill-tag">Auto-filled</span>}
          </label>
          <input
            type="text"
            placeholder="Acme Corporation"
            value={company.company_name}
            onChange={e => update('company_name', e.target.value)}
          />
        </div>

        {/* Industry — always show */}
        <div className="form-group required">
          <label>Industry</label>
          <select value={company.industry} onChange={e => update('industry', e.target.value)}>
            <option value="">Select industry...</option>
            {INDUSTRIES.map(ind => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>

        {/* Reporting Period */}
        <div className={`form-group required ${autoFilled.has('reporting_period') ? 'autofilled' : ''}`}>
          <label>
            Reporting Period
            {autoFilled.has('reporting_period') && <span className="autofill-tag">Auto-filled</span>}
          </label>
          <input
            type="text"
            placeholder="e.g. Q1 2024 or Jan–Mar 2024"
            value={company.reporting_period}
            onChange={e => update('reporting_period', e.target.value)}
          />
        </div>

        {/* Contact Name */}
        <div className="form-group">
          <label>Contact Name</label>
          <input
            type="text"
            placeholder="Jane Smith"
            value={company.contact_name}
            onChange={e => update('contact_name', e.target.value)}
          />
        </div>

        {/* Contact Email */}
        <div className="form-group">
          <label>Contact Email</label>
          <input
            type="email"
            placeholder="jane@company.com"
            value={company.contact_email}
            onChange={e => update('contact_email', e.target.value)}
          />
        </div>

        {/* Additional Notes */}
        <div className="form-group full-width">
          <label>Additional Notes</label>
          <textarea
            placeholder="Any additional context for the report..."
            value={company.additional_notes}
            onChange={e => update('additional_notes', e.target.value)}
            rows={2}
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
