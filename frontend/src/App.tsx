import React, { useState } from 'react';
import { Leaf, RotateCcw } from 'lucide-react';
import InputSection from './components/InputSection';
import ExtractedDataCard from './components/ExtractedDataCard';
import EmissionsResult from './components/EmissionsResult';
import ReportSection from './components/ReportSection';
import { ProcessResponse } from './types';
import './App.css';

export default function App() {
  const [result, setResult] = useState<ProcessResponse | null>(null);

  const handleReset = () => setResult(null);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <Leaf size={28} className="logo-icon" />
            <div>
              <h1>Carbon Intelligence</h1>
              <p>AI-powered GHG emissions analysis</p>
            </div>
          </div>
          {result && (
            <button className="btn-ghost" onClick={handleReset}>
              <RotateCcw size={16} /> New Analysis
            </button>
          )}
        </div>
      </header>

      <main className="app-main">
        {!result ? (
          <div className="landing">
            <div className="landing-hero">
              <h2>Analyze Your Carbon Footprint</h2>
              <p>
                Upload an invoice or paste document text. Our AI extracts emissions data
                and calculates your Scope 1, 2, and 3 greenhouse gas emissions instantly.
              </p>
            </div>
            <div className="input-wrapper">
              <InputSection onResult={setResult} />
            </div>
          </div>
        ) : (
          <div className="results-layout">
            <div className="results-left">
              <ExtractedDataCard data={result.extracted_data} />
              <ReportSection
                extractedData={result.extracted_data}
                emissionResult={result.emission_result}
              />
            </div>
            <div className="results-right">
              <EmissionsResult result={result.emission_result} />
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Carbon Intelligence · Emissions calculated using IPCC/EPA/DEFRA factors · For professional review</p>
      </footer>
    </div>
  );
}
