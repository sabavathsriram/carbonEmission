import React, { useState } from 'react';
import {
  CheckCircle2, Edit3, RotateCcw, AlertTriangle,
  Loader2, User, Zap, Fuel, Truck, Trash2, FileText,
  Calendar, Hash, DollarSign
} from 'lucide-react';
import type { ExtractedData, ValidationResult, ValidationIssue } from '../types';
import { revalidateData } from '../api';

interface Props {
  extracted: ExtractedData;
  validation: ValidationResult;
  onApproved: (data: ExtractedData, revalidated: import('../types').ProcessResponse) => void;
}

const FUEL_TYPES = ['diesel', 'petrol', 'natural_gas', 'lpg', 'lng', 'other'];
const TRANSPORT_MODES = ['road', 'air', 'rail', 'sea'];

function FieldWarning({ issues, field }: { issues: ValidationIssue[]; field: string }) {
  const fieldIssues = issues.filter(i => i.field === field);
  if (!fieldIssues.length) return null;
  return (
    <div className="field-issues">
      {fieldIssues.map((issue, i) => (
        <span key={i} className={`field-issue-badge ${issue.severity}`}>
          {issue.severity === 'error' ? '✕' : '⚠'} {issue.message}
        </span>
      ))}
    </div>
  );
}

export default function HITLReview({ extracted, validation, onApproved }: Props) {
  const [editing, setEditing] = useState(!validation.is_valid); // auto-open edit if errors
  const [data, setData] = useState<ExtractedData>({ ...extracted });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const update = (field: keyof ExtractedData, value: string | number | null) => {
    setData(prev => ({ ...prev, [field]: value === '' ? null : value }));
  };

  const parseNum = (val: string): number | null => {
    const n = parseFloat(val);
    return isNaN(n) ? null : n;
  };

  const hasErrors = validation.issues.some(i => i.severity === 'error');

  const handleApprove = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await revalidateData(data, true);
      if (!result.validation.is_valid) {
        setError('Validation errors remain. Please correct all errors before approving.');
        setEditing(true);
        setLoading(false);
        return;
      }
      onApproved(data, result);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Revalidation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEdits = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await revalidateData(data, false);
      // Update local validation state by calling parent with updated result
      onApproved(data, result); // parent will check if approved
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Revalidation failed.');
    } finally {
      setLoading(false);
    }
  };

  const fieldClass = (field: string) => {
    const hasError = validation.issues.some(i => i.field === field && i.severity === 'error');
    const hasWarn = validation.issues.some(i => i.field === field && i.severity === 'warning');
    return hasError ? 'field-error' : hasWarn ? 'field-warn' : '';
  };

  return (
    <div className="card hitl-card">
      <div className="hitl-header">
        <h2 className="section-title">
          <User size={20} />
          Human Review &amp; Approval
        </h2>
        <div className="hitl-actions">
          {!editing ? (
            <button className="btn-outline" onClick={() => setEditing(true)}>
              <Edit3 size={15} /> Edit Values
            </button>
          ) : (
            <button className="btn-outline" onClick={() => { setEditing(false); setData({ ...extracted }); }}>
              <RotateCcw size={15} /> Reset
            </button>
          )}
        </div>
      </div>

      {hasErrors && !editing && (
        <div className="hitl-alert">
          <AlertTriangle size={16} />
          Validation errors detected. Edit values to correct them before approving.
        </div>
      )}

      {editing ? (
        /* ---- EDIT MODE ---- */
        <div className="hitl-edit-grid">
          {/* Document Info */}
          <div className="hitl-section">
            <h3 className="hitl-section-title"><FileText size={14} /> Document Info</h3>
            <div className="hitl-fields">
              <div className={`hitl-field ${fieldClass('vendor_name')}`}>
                <label>Vendor Name</label>
                <input
                  type="text"
                  value={data.vendor_name || ''}
                  onChange={e => update('vendor_name', e.target.value)}
                  placeholder="e.g. PowerGrid Energy"
                />
                <FieldWarning issues={validation.issues} field="vendor_name" />
              </div>
              <div className={`hitl-field ${fieldClass('invoice_number')}`}>
                <label><Hash size={12} /> Invoice Number</label>
                <input
                  type="text"
                  value={data.invoice_number || ''}
                  onChange={e => update('invoice_number', e.target.value)}
                  placeholder="e.g. INV-2024-001"
                />
              </div>
              <div className={`hitl-field ${fieldClass('invoice_date')}`}>
                <label><Calendar size={12} /> Invoice Date</label>
                <input
                  type="text"
                  value={data.invoice_date || ''}
                  onChange={e => update('invoice_date', e.target.value)}
                  placeholder="YYYY-MM-DD"
                />
                <FieldWarning issues={validation.issues} field="invoice_date" />
              </div>
              <div className={`hitl-field ${fieldClass('total_amount')}`}>
                <label><DollarSign size={12} /> Total Amount</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    min="0"
                    value={data.total_amount ?? ''}
                    onChange={e => update('total_amount', parseNum(e.target.value))}
                    placeholder="0.00"
                  />
                  <input
                    type="text"
                    value={data.currency || 'USD'}
                    onChange={e => update('currency', e.target.value)}
                    className="unit-input"
                    maxLength={3}
                  />
                </div>
                <FieldWarning issues={validation.issues} field="total_amount" />
              </div>
            </div>
          </div>

          {/* Emissions Data */}
          <div className="hitl-section">
            <h3 className="hitl-section-title"><Zap size={14} /> Electricity (Scope 2)</h3>
            <div className="hitl-fields">
              <div className={`hitl-field ${fieldClass('energy_kwh')}`}>
                <label>Electricity Consumed</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    min="0"
                    value={data.energy_kwh ?? ''}
                    onChange={e => update('energy_kwh', parseNum(e.target.value))}
                    placeholder="0"
                  />
                  <span className="unit-label">kWh</span>
                </div>
                <FieldWarning issues={validation.issues} field="energy_kwh" />
              </div>
            </div>
          </div>

          <div className="hitl-section">
            <h3 className="hitl-section-title"><Fuel size={14} /> Fuel (Scope 1)</h3>
            <div className="hitl-fields">
              <div className={`hitl-field ${fieldClass('fuel_liters')}`}>
                <label>Fuel Volume</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    min="0"
                    value={data.fuel_liters ?? ''}
                    onChange={e => update('fuel_liters', parseNum(e.target.value))}
                    placeholder="0"
                  />
                  <span className="unit-label">L</span>
                </div>
                <FieldWarning issues={validation.issues} field="fuel_liters" />
              </div>
              <div className={`hitl-field ${fieldClass('fuel_type')}`}>
                <label>Fuel Type</label>
                <select
                  value={data.fuel_type || ''}
                  onChange={e => update('fuel_type', e.target.value)}
                >
                  <option value="">Select fuel type...</option>
                  {FUEL_TYPES.map(f => <option key={f} value={f}>{f}</option>)}
                </select>
                <FieldWarning issues={validation.issues} field="fuel_type" />
              </div>
            </div>
          </div>

          <div className="hitl-section">
            <h3 className="hitl-section-title"><Truck size={14} /> Transport (Scope 3)</h3>
            <div className="hitl-fields">
              <div className={`hitl-field ${fieldClass('distance_km')}`}>
                <label>Distance</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    min="0"
                    value={data.distance_km ?? ''}
                    onChange={e => update('distance_km', parseNum(e.target.value))}
                    placeholder="0"
                  />
                  <span className="unit-label">km</span>
                </div>
                <FieldWarning issues={validation.issues} field="distance_km" />
              </div>
              <div className={`hitl-field ${fieldClass('transport_mode')}`}>
                <label>Transport Mode</label>
                <select
                  value={data.transport_mode || ''}
                  onChange={e => update('transport_mode', e.target.value)}
                >
                  <option value="">Select mode...</option>
                  {TRANSPORT_MODES.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
                <FieldWarning issues={validation.issues} field="transport_mode" />
              </div>
            </div>
          </div>

          <div className="hitl-section">
            <h3 className="hitl-section-title"><Trash2 size={14} /> Waste (Scope 3)</h3>
            <div className="hitl-fields">
              <div className={`hitl-field ${fieldClass('waste_kg')}`}>
                <label>Waste Weight</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    min="0"
                    value={data.waste_kg ?? ''}
                    onChange={e => update('waste_kg', parseNum(e.target.value))}
                    placeholder="0"
                  />
                  <span className="unit-label">kg</span>
                </div>
                <FieldWarning issues={validation.issues} field="waste_kg" />
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* ---- VIEW MODE ---- */
        <div className="hitl-view">
          <div className="hitl-view-grid">
            {[
              { label: 'Vendor', value: data.vendor_name, field: 'vendor_name' },
              { label: 'Invoice #', value: data.invoice_number, field: 'invoice_number' },
              { label: 'Date', value: data.invoice_date, field: 'invoice_date' },
              { label: 'Amount', value: data.total_amount != null ? `${data.total_amount.toLocaleString()} ${data.currency || ''}` : null, field: 'total_amount' },
              { label: 'Electricity', value: data.energy_kwh != null ? `${data.energy_kwh.toLocaleString()} kWh` : null, field: 'energy_kwh' },
              { label: 'Fuel', value: data.fuel_liters != null ? `${data.fuel_liters.toLocaleString()} L (${data.fuel_type || '—'})` : null, field: 'fuel_liters' },
              { label: 'Distance', value: data.distance_km != null ? `${data.distance_km.toLocaleString()} km (${data.transport_mode || '—'})` : null, field: 'distance_km' },
              { label: 'Waste', value: data.waste_kg != null ? `${data.waste_kg.toLocaleString()} kg` : null, field: 'waste_kg' },
            ].map(({ label, value, field }) => (
              <div key={field} className={`hitl-view-row ${fieldClass(field)}`}>
                <span className="hitl-view-label">{label}</span>
                <span className={`hitl-view-value ${!value ? 'missing' : ''}`}>
                  {value || <span className="missing-badge">Missing</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="error-banner" style={{ marginTop: 12 }}>
          <AlertTriangle size={15} /> {error}
        </div>
      )}

      {/* Action buttons */}
      <div className="hitl-footer">
        {editing && (
          <button
            className="btn-secondary"
            onClick={handleSaveEdits}
            disabled={loading}
          >
            {loading ? <Loader2 size={16} className="spin" /> : <Edit3 size={16} />}
            Save &amp; Revalidate
          </button>
        )}
        <button
          className="btn-approve"
          onClick={handleApprove}
          disabled={loading || hasErrors}
          title={hasErrors ? 'Correct all errors before approving' : ''}
        >
          {loading ? (
            <><Loader2 size={16} className="spin" /> Processing...</>
          ) : (
            <><CheckCircle2 size={16} /> Approve &amp; Calculate Emissions</>
          )}
        </button>
      </div>

      {hasErrors && (
        <p className="hitl-block-note">
          ⚠ Report generation is disabled until all validation errors are corrected.
        </p>
      )}
    </div>
  );
}
