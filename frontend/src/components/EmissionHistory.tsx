import React, { useEffect, useState } from 'react';
import { History, TrendingUp, TrendingDown, Minus, RefreshCw, FileText, Award } from 'lucide-react';
import { getEmissionHistory } from '../api';
import type { EmissionRecord } from '../types';

function TrendBadge({ record }: { record: EmissionRecord }) {
  if (record.trend === 'baseline') {
    return <span className="trend-badge baseline"><Minus size={11} /> Baseline</span>;
  }
  if (record.trend === 'decreased') {
    return (
      <span className="trend-badge decreased">
        <TrendingDown size={11} />
        {Math.abs(record.delta_pct ?? 0).toFixed(1)}% less
        <span className="trend-kg">({Math.abs(record.delta_kg ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kg)</span>
      </span>
    );
  }
  if (record.trend === 'increased') {
    return (
      <span className="trend-badge increased">
        <TrendingUp size={11} />
        {Math.abs(record.delta_pct ?? 0).toFixed(1)}% more
        <span className="trend-kg">(+{Math.abs(record.delta_kg ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kg)</span>
      </span>
    );
  }
  return null;
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso; }
}

export default function EmissionHistory() {
  const [records, setRecords] = useState<EmissionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await getEmissionHistory();
      setRecords(res.records);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // Summary stats
  const totalRecords = records.length;
  const latestTotal  = records[0]?.total_kg_co2e ?? 0;
  const prevTotal    = records[1]?.total_kg_co2e ?? null;
  const overallDelta = prevTotal !== null ? latestTotal - prevTotal : null;
  const overallPct   = prevTotal ? (overallDelta! / prevTotal * 100) : null;

  return (
    <div className="card">
      <div className="history-header">
        <h2 className="section-title"><History size={20} /> Emission History</h2>
        <button className="btn-outline" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {/* Summary strip */}
      {totalRecords > 0 && (
        <div className="history-summary">
          <div className="hs-item">
            <span className="hs-label">Total Records</span>
            <span className="hs-value">{totalRecords}</span>
          </div>
          <div className="hs-item">
            <span className="hs-label">Latest Emissions</span>
            <span className="hs-value">{(latestTotal / 1000).toFixed(3)}t CO₂e</span>
          </div>
          {overallDelta !== null && overallPct !== null && (
            <div className="hs-item">
              <span className="hs-label">vs Previous</span>
              <span className={`hs-value ${overallDelta < 0 ? 'green' : overallDelta > 0 ? 'red' : ''}`}>
                {overallDelta < 0 ? '▼' : overallDelta > 0 ? '▲' : '='}{' '}
                {Math.abs(overallPct).toFixed(1)}%
              </span>
            </div>
          )}
          <div className="hs-item">
            <span className="hs-label">Latest ESG</span>
            <span className="hs-value">{records[0]?.esg_score ?? '—'}/100</span>
          </div>
        </div>
      )}

      {loading && (
        <div className="history-loading">
          <div className="extracting-spinner" style={{ width: 28, height: 28 }} />
          <span>Loading history...</span>
        </div>
      )}

      {error && <div className="error-banner" style={{ marginTop: 8 }}>{error}</div>}

      {!loading && records.length === 0 && !error && (
        <div className="history-empty">
          <History size={32} style={{ color: 'var(--mid)', marginBottom: 8 }} />
          <p>No emission records yet.</p>
          <p className="history-empty-sub">Approve an analysis to save it here.</p>
        </div>
      )}

      {!loading && records.length > 0 && (
        <div className="history-table">
          <div className="ht-header">
            <span>Date</span>
            <span>Source</span>
            <span>Total CO₂e</span>
            <span>Scope 1</span>
            <span>Scope 2</span>
            <span>Scope 3</span>
            <span>ESG</span>
            <span>vs Previous</span>
          </div>
          {records.map((rec, i) => (
            <div key={rec.record_id} className={`ht-row ${i === 0 ? 'ht-latest' : ''}`}>
              <span className="ht-date">{formatDate(rec.timestamp)}</span>
              <span className="ht-source">
                <FileText size={12} />
                {rec.source_filename.length > 20
                  ? rec.source_filename.slice(0, 18) + '…'
                  : rec.source_filename}
              </span>
              <span className="ht-total">
                <strong>{rec.total_kg_co2e.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg</strong>
              </span>
              <span className="ht-scope s1">{rec.scope1_kg_co2e.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
              <span className="ht-scope s2">{rec.scope2_kg_co2e.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
              <span className="ht-scope s3">{rec.scope3_kg_co2e.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
              <span className="ht-esg">
                <Award size={12} /> {rec.esg_score}
              </span>
              <span><TrendBadge record={rec} /></span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
