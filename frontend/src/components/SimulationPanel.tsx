import React, { useState } from 'react';
import { FlaskConical, ChevronDown, ChevronUp, TrendingDown, DollarSign, Leaf } from 'lucide-react';
import type { SimulationResult } from '../types';

interface Props { simulations: SimulationResult[]; }

const CATEGORY_COLORS: Record<string, string> = {
  'Fuel Efficiency': '#e74c3c',
  'Energy Transition': '#f39c12',
  'Operational Efficiency': '#3498db',
  'Logistics Optimization': '#9b59b6',
  'Waste Management': '#1a7f5a',
};

export default function SimulationPanel({ simulations }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  if (!simulations.length) return null;

  return (
    <div className="card">
      <h2 className="section-title"><FlaskConical size={20} /> What-If Simulation</h2>
      <p className="panel-desc">Projected impact of operational optimizations — all scenarios maintain current business output.</p>
      <div className="sim-list">
        {simulations.map(sim => (
          <div key={sim.id} className={`sim-card ${expanded === sim.id ? 'expanded' : ''}`}>
            <div className="sim-header" onClick={() => setExpanded(expanded === sim.id ? null : sim.id)}>
              <div className="sim-left">
                <span className="sim-category" style={{ background: CATEGORY_COLORS[sim.category] || '#7f8c8d' }}>
                  {sim.category}
                </span>
                <span className="sim-title">{sim.title}</span>
              </div>
              <div className="sim-right">
                <span className="sim-reduction">
                  <TrendingDown size={13} /> {sim.emission_reduction_tonnes.toFixed(2)}t CO₂e
                </span>
                {expanded === sim.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
            </div>
            {expanded === sim.id && (
              <div className="sim-body">
                <p className="sim-desc">{sim.description}</p>
                <div className="sim-metrics">
                  <div className="sim-metric">
                    <TrendingDown size={14} style={{ color: '#1a7f5a' }} />
                    <div>
                      <span className="sm-val">{sim.emission_reduction_kg.toLocaleString()} kg</span>
                      <span className="sm-label">Emission Reduction</span>
                    </div>
                  </div>
                  <div className="sim-metric">
                    <DollarSign size={14} style={{ color: '#f39c12' }} />
                    <div>
                      <span className="sm-val">${sim.cost_saving_usd.toLocaleString()}</span>
                      <span className="sm-label">Est. Cost Saving</span>
                    </div>
                  </div>
                  <div className="sim-metric">
                    <Leaf size={14} style={{ color: '#1a7f5a' }} />
                    <div>
                      <span className="sm-val">+{sim.esg_score_improvement.toFixed(1)} pts</span>
                      <span className="sm-label">ESG Improvement</span>
                    </div>
                  </div>
                </div>
                <div className="sim-note">
                  <span className="maintains-badge">✓ Maintains Operational Output</span>
                  <p>{sim.operational_note}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
