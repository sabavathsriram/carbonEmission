import React from 'react';
import { Leaf, BarChart2, Info } from 'lucide-react';
import { EmissionResult } from '../types';

interface Props {
  result: EmissionResult;
}

function ScopeBar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="scope-bar-row">
      <div className="scope-bar-label">
        <span>{label}</span>
        <span className="scope-value">{value.toLocaleString(undefined, { maximumFractionDigits: 2 })} kg CO₂e</span>
      </div>
      <div className="scope-bar-track">
        <div className="scope-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="scope-pct">{pct.toFixed(1)}%</span>
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? '#1a7f5a' : pct >= 45 ? '#f39c12' : '#e74c3c';
  const label = pct >= 70 ? 'High' : pct >= 45 ? 'Medium' : 'Low';
  return (
    <div className="confidence-badge" style={{ borderColor: color }}>
      <div className="confidence-ring" style={{ '--pct': pct, '--color': color } as React.CSSProperties}>
        <span className="confidence-pct" style={{ color }}>{pct}%</span>
      </div>
      <div>
        <p className="confidence-label">Confidence</p>
        <p className="confidence-level" style={{ color }}>{label}</p>
      </div>
    </div>
  );
}

export default function EmissionsResult({ result }: Props) {
  const totalTonnes = result.total_kg_co2e / 1000;

  return (
    <div className="card emissions-card">
      <h2 className="section-title">
        <Leaf size={20} />
        Emissions Result
      </h2>

      <div className="emissions-hero">
        <div className="total-emissions">
          <p className="total-label">Total Emissions</p>
          <p className="total-value">
            {result.total_kg_co2e.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
          <p className="total-unit">kg CO₂e</p>
          <p className="total-tonnes">≈ {totalTonnes.toFixed(3)} tonnes CO₂e</p>
        </div>
        <ConfidenceBadge score={result.confidence_score} />
      </div>

      <div className="scope-bars">
        <ScopeBar label="Scope 1 — Direct" value={result.scope1_kg_co2e} total={result.total_kg_co2e} color="#e74c3c" />
        <ScopeBar label="Scope 2 — Electricity" value={result.scope2_kg_co2e} total={result.total_kg_co2e} color="#f39c12" />
        <ScopeBar label="Scope 3 — Indirect" value={result.scope3_kg_co2e} total={result.total_kg_co2e} color="#3498db" />
      </div>

      {result.breakdown.length > 0 && (
        <div className="breakdown">
          <h3 className="sub-title"><BarChart2 size={15} /> Breakdown</h3>
          <div className="breakdown-table">
            <div className="bt-header">
              <span>Category</span>
              <span>Quantity</span>
              <span>Factor</span>
              <span>kg CO₂e</span>
            </div>
            {result.breakdown.map((item, i) => (
              <div key={i} className="bt-row">
                <span>{item.category}</span>
                <span>{item.quantity.toLocaleString()} {item.unit}</span>
                <span>{item.emission_factor.toFixed(4)}</span>
                <span className="bt-co2">{item.kg_co2e.toLocaleString(undefined, { maximumFractionDigits: 3 })}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="methodology-note">
        <Info size={14} />
        <p>{result.methodology_notes}</p>
      </div>
    </div>
  );
}
