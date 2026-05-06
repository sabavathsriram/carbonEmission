import React, { useState } from 'react';
import { Bell, Zap, Fuel, Truck, AlertTriangle, Shield, Trash2, X } from 'lucide-react';
import type { SmartAlert } from '../types';

interface Props { alerts: SmartAlert[]; }

const ICON_MAP: Record<string, React.ReactNode> = {
  zap: <Zap size={15} />, fuel: <Fuel size={15} />, truck: <Truck size={15} />,
  'alert-triangle': <AlertTriangle size={15} />, shield: <Shield size={15} />, trash: <Trash2 size={15} />,
};

const SEV_CLASS: Record<string, string> = { high: 'alert-high', medium: 'alert-medium', low: 'alert-low' };

export default function AlertsPanel({ alerts }: Props) {
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());
  const visible = alerts.filter((_, i) => !dismissed.has(i));
  if (!visible.length) return null;

  return (
    <div className="card">
      <h2 className="section-title"><Bell size={20} /> Smart Alerts <span className="alert-count">{visible.length}</span></h2>
      <div className="alerts-list">
        {alerts.map((alert, i) => dismissed.has(i) ? null : (
          <div key={i} className={`alert-item ${SEV_CLASS[alert.severity]}`}>
            <span className="alert-icon">{ICON_MAP[alert.icon] || <AlertTriangle size={15} />}</span>
            <div className="alert-content">
              <p className="alert-title">{alert.title}</p>
              <p className="alert-msg">{alert.message}</p>
            </div>
            <button className="alert-dismiss" onClick={() => setDismissed(prev => new Set([...prev, i]))}>
              <X size={13} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
