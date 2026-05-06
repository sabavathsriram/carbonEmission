import React from 'react';
import { Upload, Brain, ShieldCheck, UserCheck, Calculator, FileDown, Check } from 'lucide-react';
import type { WorkflowStage } from '../types';

const STEPS: Array<{ id: WorkflowStage | 'done'; label: string; icon: React.ReactNode }> = [
  { id: 'input',      label: 'Upload',     icon: <Upload size={14} /> },
  { id: 'extracting', label: 'AI Extract', icon: <Brain size={14} /> },
  { id: 'review',     label: 'Validate',   icon: <ShieldCheck size={14} /> },
  { id: 'approved',   label: 'Approved',   icon: <UserCheck size={14} /> },
  { id: 'report',     label: 'Report',     icon: <FileDown size={14} /> },
];

const STAGE_INDEX: Record<string, number> = {
  input: 0,
  extracting: 1,
  review: 2,
  approved: 3,
  report: 4,
};

interface Props {
  stage: WorkflowStage;
}

export default function WorkflowStepper({ stage }: Props) {
  const current = STAGE_INDEX[stage] ?? 0;

  return (
    <div className="stepper">
      {STEPS.map((step, idx) => {
        const done = idx < current;
        const active = idx === current;
        return (
          <React.Fragment key={step.id}>
            <div className={`step ${done ? 'done' : active ? 'active' : 'pending'}`}>
              <div className="step-circle">
                {done ? <Check size={13} /> : step.icon}
              </div>
              <span className="step-label">{step.label}</span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`step-connector ${done ? 'done' : ''}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
