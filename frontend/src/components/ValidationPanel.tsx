import React from 'react';
import { AlertTriangle, XCircle, Info, CheckCircle, ShieldCheck, ShieldAlert } from 'lucide-react';
import type { ValidationResult, ValidationIssue, ValidationSeverity } from '../types';

interface Props {
  validation: ValidationResult;
  confidenceScore: number;
}

const SEVERITY_CONFIG: Record<ValidationSeverity, {
  icon: React.ReactNode;
  label: string;
  rowClass: string;
}> = {
  error: {
    icon: <XCircle size={15} />,
    label: 'Error',
    rowClass: 'vi-error',
  },
  warning: {
    icon: <AlertTriangle size={15} />,
    label: 'Warning',
    rowClass: 'vi-warning',
  },
  info: {
    icon: <Info size={15} />,
    label: 'Info',
    rowClass: 'vi-info',
  },
};

function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const level = pct >= 80 ? 'High' : pct >= 50 ? 'Medium' : 'Low';
  const color = pct >= 80 ? 'var(--primary)' : pct >= 50 ? 'var(--warning)' : 'var(--danger)';

  return (
    <div className="conf-meter">
      <div className="conf-meter-header">
        <span className="conf-meter-label">Confidence Score</span>
        <span className="conf-meter-value" style={{ color }}>
          {pct}% — {level}
        </span>
      </div>
      <div className="conf-meter-track">
        <div
          className="conf-meter-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

function IssueRow({ issue }: { issue: ValidationIssue }) {
  const cfg = SEVERITY_CONFIG[issue.severity];
  return (
    <div className={`vi-row ${cfg.rowClass}`}>
      <span className="vi-icon">{cfg.icon}</span>
      <div className="vi-content">
        <span className="vi-message">{issue.message}</span>
        {issue.current_value !== undefined && issue.current_value !== null && (
          <span className="vi-meta">
            Current: {issue.current_value}
            {issue.suggested_value !== undefined && issue.suggested_value !== null && (
              <> → Suggested: {issue.suggested_value}</>
            )}
          </span>
        )}
      </div>
      <span className="vi-badge">{cfg.label}</span>
    </div>
  );
}

export default function ValidationPanel({ validation, confidenceScore }: Props) {
  const errors = validation.issues.filter(i => i.severity === 'error');
  const warnings = validation.issues.filter(i => i.severity === 'warning');
  const infos = validation.issues.filter(i => i.severity === 'info');

  const overallStatus = !validation.is_valid
    ? { icon: <ShieldAlert size={18} />, label: 'Validation Failed — Errors Must Be Corrected', cls: 'status-error' }
    : validation.requires_review
    ? { icon: <AlertTriangle size={18} />, label: 'Review Recommended — Warnings Detected', cls: 'status-warning' }
    : { icon: <ShieldCheck size={18} />, label: 'Validation Passed', cls: 'status-ok' };

  return (
    <div className="card vp-card">
      <h2 className="section-title">
        <ShieldCheck size={20} />
        AI Validation &amp; Guardrails
      </h2>

      {/* Overall status banner */}
      <div className={`vp-status ${overallStatus.cls}`}>
        {overallStatus.icon}
        <span>{overallStatus.label}</span>
      </div>

      {/* Confidence meter */}
      <ConfidenceMeter score={confidenceScore} />

      {/* Issue counts */}
      {validation.issues.length > 0 && (
        <div className="vp-counts">
          {errors.length > 0 && (
            <span className="vp-count error">{errors.length} Error{errors.length > 1 ? 's' : ''}</span>
          )}
          {warnings.length > 0 && (
            <span className="vp-count warning">{warnings.length} Warning{warnings.length > 1 ? 's' : ''}</span>
          )}
          {infos.length > 0 && (
            <span className="vp-count info">{infos.length} Notice{infos.length > 1 ? 's' : ''}</span>
          )}
        </div>
      )}

      {/* Issue list */}
      {validation.issues.length > 0 ? (
        <div className="vi-list">
          {errors.map((issue, i) => <IssueRow key={`e-${i}`} issue={issue} />)}
          {warnings.map((issue, i) => <IssueRow key={`w-${i}`} issue={issue} />)}
          {infos.map((issue, i) => <IssueRow key={`i-${i}`} issue={issue} />)}
        </div>
      ) : (
        <div className="vp-clean">
          <CheckCircle size={16} />
          <span>No issues detected — all values within expected ranges</span>
        </div>
      )}
    </div>
  );
}
