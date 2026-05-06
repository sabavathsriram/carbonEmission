import React, { useState } from 'react';
import { TrendingUp, ChevronDown, ChevronUp, CheckCircle, DollarSign } from 'lucide-react';
import type { Recommendation } from '../types';

interface Props { recommendations: Recommendation[]; }

const PRIORITY_CONFIG = {
  high:   { label: 'High ROI',    cls: 'priority-high' },
  medium: { label: 'Medium ROI',  cls: 'priority-medium' },
  low:    { label: 'Strategic',   cls: 'priority-low' },
};

export default function RecommendationsPanel({ recommendations }: Props) {
  const [expanded, setExpanded] = useState<string | null>(recommendations[0]?.id || null);
  if (!recommendations.length) return null;

  return (
    <div className="card">
      <h2 className="section-title">
        <TrendingUp size={20} />
        Revenue &amp; Efficiency Opportunities
      </h2>
      <p className="panel-desc">
        Operational improvements that reduce costs and unlock revenue — all while maintaining
        current production capacity and service levels.
      </p>
      <div className="rec-list">
        {recommendations.map(rec => {
          const cfg = PRIORITY_CONFIG[rec.priority];
          const revenueImpact = (rec as any).revenue_impact as string | undefined;
          return (
            <div key={rec.id} className={`rec-card ${expanded === rec.id ? 'expanded' : ''}`}>
              <div className="rec-header" onClick={() => setExpanded(expanded === rec.id ? null : rec.id)}>
                <div className="rec-left">
                  <span className={`rec-priority ${cfg.cls}`}>{cfg.label}</span>
                  <span className="rec-category-tag">{rec.category}</span>
                  <span className="rec-title">{rec.title}</span>
                </div>
                <div className="rec-right-meta">
                  {revenueImpact && (
                    <span className="rec-revenue-badge">
                      <DollarSign size={11} />{revenueImpact}
                    </span>
                  )}
                  {expanded === rec.id ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                </div>
              </div>

              {expanded === rec.id && (
                <div className="rec-body">
                  <div className="rec-insight">
                    <strong>Business Case:</strong> {rec.insight}
                  </div>
                  <div className="rec-action">
                    <strong>Implementation:</strong> {rec.action}
                  </div>
                  <div className="rec-impact">
                    <strong>Financial &amp; ESG Impact:</strong> {rec.impact}
                  </div>
                  <div className="rec-footer-row">
                    {rec.maintains_output && (
                      <div className="rec-maintains">
                        <CheckCircle size={13} /> Operational performance maintained — no output reduction
                      </div>
                    )}
                    {revenueImpact && (
                      <div className="rec-revenue-highlight">
                        <DollarSign size={13} /> Estimated benefit: <strong>{revenueImpact}</strong>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
