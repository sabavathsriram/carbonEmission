import React from 'react';
import { Link2, CheckCircle, AlertCircle } from 'lucide-react';
import type { TraceabilityItem } from '../types';

interface Props { items: TraceabilityItem[]; }

export default function TraceabilityPanel({ items }: Props) {
  if (!items.length) return null;
  return (
    <div className="card">
      <h2 className="section-title"><Link2 size={20} /> Data Source Traceability</h2>
      <p className="panel-desc">Full audit trail of extracted values — source document, extraction method, and confidence level.</p>
      <div className="trace-table">
        <div className="trace-header">
          <span>Field</span><span>Value</span><span>Source</span><span>Method</span><span>Confidence</span>
        </div>
        {items.map((item, i) => (
          <div key={i} className="trace-row">
            <span className="trace-field">{item.field}</span>
            <span className="trace-value">{item.value}</span>
            <span className="trace-source">{item.source}</span>
            <span className="trace-method">{item.extraction_method}</span>
            <span className={`trace-conf ${item.confidence.toLowerCase()}`}>
              {item.confidence === 'High' ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
              {item.confidence}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
