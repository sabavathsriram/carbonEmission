import React from 'react';
import { Award, TrendingUp, Database, Zap } from 'lucide-react';
import type { ESGData, EmissionResult } from '../types';

interface Props { esg: ESGData; emissions: EmissionResult; }

export default function ESGScoreCard({ esg, emissions }: Props) {
  const kpis = [
    { label: 'Total Emissions', value: `${(emissions.total_kg_co2e/1000).toFixed(2)}t`, sub: 'CO₂e', icon: <Zap size={18} />, color: '#e74c3c' },
    { label: 'ESG Score', value: `${esg.score}`, sub: `Grade ${esg.grade}`, icon: <Award size={18} />, color: esg.color },
    { label: 'Confidence', value: `${Math.round(emissions.confidence_score * 100)}%`, sub: emissions.confidence_score >= 0.8 ? 'High' : emissions.confidence_score >= 0.5 ? 'Medium' : 'Low', icon: <TrendingUp size={18} />, color: emissions.confidence_score >= 0.8 ? '#1a7f5a' : emissions.confidence_score >= 0.5 ? '#f39c12' : '#e74c3c' },
    { label: 'Data Completeness', value: `${esg.breakdown.data_completeness}%`, sub: 'Fields extracted', icon: <Database size={18} />, color: '#3498db' },
  ];

  return (
    <div className="esg-card">
      <div className="esg-header">
        <div className="esg-score-circle" style={{ borderColor: esg.color }}>
          <span className="esg-score-num" style={{ color: esg.color }}>{esg.score}</span>
          <span className="esg-score-label">ESG</span>
        </div>
        <div className="esg-info">
          <div className="esg-grade" style={{ background: esg.color }}>{esg.grade}</div>
          <p className="esg-label-text">{esg.label}</p>
          <p className="esg-sub">Operational Carbon Intelligence Score</p>
        </div>
      </div>

      <div className="kpi-grid">
        {kpis.map(kpi => (
          <div key={kpi.label} className="kpi-card">
            <div className="kpi-icon" style={{ color: kpi.color }}>{kpi.icon}</div>
            <div className="kpi-value" style={{ color: kpi.color }}>{kpi.value}</div>
            <div className="kpi-label">{kpi.label}</div>
            <div className="kpi-sub">{kpi.sub}</div>
          </div>
        ))}
      </div>

      <div className="esg-breakdown">
        <div className="esg-breakdown-row">
          <span>Emission Intensity</span>
          <span className={`intensity-badge ${esg.breakdown.emission_intensity.toLowerCase()}`}>
            {esg.breakdown.emission_intensity}
          </span>
        </div>
      </div>
    </div>
  );
}
