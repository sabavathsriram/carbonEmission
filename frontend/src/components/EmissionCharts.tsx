import React from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend, CartesianGrid,
} from 'recharts';
import { BarChart2 } from 'lucide-react';
import type { EmissionResult, Forecast } from '../types';

interface Props { emissions: EmissionResult; forecast?: Forecast; }

const SCOPE_COLORS = ['#e74c3c', '#f39c12', '#3498db'];

const SCOPE_LABELS: Record<string, string> = {
  'Scope 1': 'Scope 1 — Direct (fuel, combustion)',
  'Scope 2': 'Scope 2 — Electricity (purchased power)',
  'Scope 3': 'Scope 3 — Indirect (transport, waste)',
};

function ScopeLegend({ data }: { data: { name: string; value: number }[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <div className="scope-legend">
      {data.map((d, i) => (
        <div key={d.name} className="scope-legend-item">
          <span className="scope-legend-dot" style={{ background: SCOPE_COLORS[i % 3] }} />
          <div className="scope-legend-text">
            <span className="scope-legend-name">{SCOPE_LABELS[d.name] || d.name}</span>
            <span className="scope-legend-val">
              {d.value.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg
              {total > 0 && <> &middot; {(d.value / total * 100).toFixed(1)}%</>}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function EmissionCharts({ emissions, forecast }: Props) {
  const pieData = [
    { name: 'Scope 1', value: emissions.scope1_kg_co2e },
    { name: 'Scope 2', value: emissions.scope2_kg_co2e },
    { name: 'Scope 3', value: emissions.scope3_kg_co2e },
  ].filter(d => d.value > 0);

  const barData = emissions.breakdown.map(b => ({
    name: b.category.replace('Scope 1 - ', '').replace('Scope 2 - ', '').replace('Scope 3 - ', ''),
    value: b.kg_co2e,
    fill: b.category.includes('Scope 1') ? '#e74c3c'
        : b.category.includes('Scope 2') ? '#f39c12'
        : '#3498db',
  }));

  return (
    <div className="card">
      <h2 className="section-title"><BarChart2 size={20} /> Emission Analytics</h2>

      <div className="charts-grid">
        {/* Scope Distribution Pie + Legend */}
        <div className="chart-box">
          <h3 className="chart-title">Scope Distribution</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={72}
                dataKey="value" labelLine={false}>
                {pieData.map((_, i) => <Cell key={i} fill={SCOPE_COLORS[i % 3]} />)}
              </Pie>
              <Tooltip formatter={(v) => [`${Number(v).toLocaleString()} kg CO2e`, '']} />
            </PieChart>
          </ResponsiveContainer>
          <ScopeLegend data={pieData} />
        </div>

        {/* Breakdown Bar */}
        {barData.length > 0 && (
          <div className="chart-box">
            <h3 className="chart-title">Emission Sources</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => [`${Number(v).toLocaleString()} kg CO2e`, 'Emissions']} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {barData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Forecast Line Chart */}
        {forecast && (
          <div className="chart-box chart-box-wide">
            <h3 className="chart-title">12-Month Emission Forecast</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={forecast.monthly_data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => [`${Number(v).toLocaleString()} kg`, '']} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="bau" stroke="#e74c3c" name="Business as Usual" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="optimized" stroke="#f39c12" name="Optimized" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                <Line type="monotone" dataKey="target" stroke="#1a7f5a" name="Target" strokeWidth={2} dot={false} strokeDasharray="3 3" />
              </LineChart>
            </ResponsiveContainer>
            {forecast.yearly_summary && (
              <div className="forecast-summary">
                <div className="fs-item">
                  <span>BAU Annual</span>
                  <strong>{(forecast.yearly_summary.bau_total_kg / 1000).toFixed(1)}t CO2e</strong>
                </div>
                <div className="fs-item green">
                  <span>Potential Saving</span>
                  <strong>{(forecast.yearly_summary.optimized_saving_kg / 1000).toFixed(1)}t CO2e</strong>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
