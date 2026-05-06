import React from 'react';
import { Database, Package } from 'lucide-react';
import { ExtractedData } from '../types';

interface Props {
  data: ExtractedData;
}

function Row({ label, value }: { label: string; value?: string | number | null }) {
  if (value === undefined || value === null || value === '') return null;
  return (
    <div className="data-row">
      <span className="data-label">{label}</span>
      <span className="data-value">{value}</span>
    </div>
  );
}

export default function ExtractedDataCard({ data }: Props) {
  return (
    <div className="card">
      <h2 className="section-title">
        <Database size={20} />
        Extracted Data
      </h2>

      <div className="data-grid">
        <Row label="Vendor" value={data.vendor_name} />
        <Row label="Invoice #" value={data.invoice_number} />
        <Row label="Date" value={data.invoice_date} />
        <Row
          label="Total Amount"
          value={data.total_amount != null ? `${data.total_amount.toLocaleString()} ${data.currency || ''}` : undefined}
        />
        <Row label="Electricity" value={data.energy_kwh != null ? `${data.energy_kwh.toLocaleString()} kWh` : undefined} />
        <Row
          label="Fuel"
          value={data.fuel_liters != null ? `${data.fuel_liters.toLocaleString()} L (${data.fuel_type || 'unknown'})` : undefined}
        />
        <Row
          label="Distance"
          value={data.distance_km != null ? `${data.distance_km.toLocaleString()} km (${data.transport_mode || 'unknown'})` : undefined}
        />
        <Row label="Waste" value={data.waste_kg != null ? `${data.waste_kg.toLocaleString()} kg` : undefined} />
      </div>

      {data.line_items && data.line_items.length > 0 && (
        <div className="line-items">
          <h3 className="sub-title">
            <Package size={15} /> Line Items
          </h3>
          <div className="line-items-table">
            <div className="li-header">
              <span>Description</span>
              <span>Qty</span>
              <span>Unit</span>
              <span>Amount</span>
            </div>
            {data.line_items.map((item, i) => (
              <div key={i} className="li-row">
                <span>{item.description}</span>
                <span>{item.quantity ?? '—'}</span>
                <span>{item.unit ?? '—'}</span>
                <span>{item.amount != null ? `${item.amount.toLocaleString()} ${item.currency || ''}` : '—'}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
