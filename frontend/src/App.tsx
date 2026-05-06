import React, { useState } from 'react';
import { Leaf, RotateCcw, LogOut, User, LayoutDashboard, PlusCircle, History } from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './components/AuthPage';
import InputSection from './components/InputSection';
import ValidationPanel from './components/ValidationPanel';
import HITLReview from './components/HITLReview';
import EmissionsResult from './components/EmissionsResult';
import ReportSection from './components/ReportSection';
import WorkflowStepper from './components/WorkflowStepper';
import ESGScoreCard from './components/ESGScoreCard';
import EmissionCharts from './components/EmissionCharts';
import SimulationPanel from './components/SimulationPanel';
import RecommendationsPanel from './components/RecommendationsPanel';
import AlertsPanel from './components/AlertsPanel';
import TraceabilityPanel from './components/TraceabilityPanel';
import EmissionHistory from './components/EmissionHistory';
import type { ProcessResponse, ExtractedData, WorkflowStage } from './types';
import './App.css';

type NavTab = 'analysis' | 'dashboard' | 'history';

function AppInner() {
  const { user, logout, isAuthenticated } = useAuth();
  const [stage, setStage]                 = useState<WorkflowStage>('input');
  const [result, setResult]               = useState<ProcessResponse | null>(null);
  const [approvedResult, setApprovedResult] = useState<ProcessResponse | null>(null);
  const [activeTab, setActiveTab]         = useState<NavTab>('analysis');

  if (!isAuthenticated) return <AuthPage />;

  const handleExtracted  = (res: ProcessResponse) => { setResult(res); setApprovedResult(null); setStage('review'); setActiveTab('analysis'); };
  const handleExtracting = () => setStage('extracting');
  const handleHITLUpdate = (data: ExtractedData, revalidated: ProcessResponse) => {
    setResult(revalidated);
    if (revalidated.validation.is_valid) { setApprovedResult(revalidated); setStage('approved'); }
  };
  const handleReset = () => { setStage('input'); setResult(null); setApprovedResult(null); setActiveTab('analysis'); };

  const active = approvedResult || result;

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <Leaf size={26} className="logo-icon" />
            <div>
              <h1>Carbon Intelligence</h1>
              <p>Enterprise ESG &amp; Emissions Platform</p>
            </div>
          </div>

          <nav className="header-nav">
            {/* Always-visible nav items */}
            <button
              className={`nav-tab ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              <PlusCircle size={14} /> Analysis
            </button>

            {active && (
              <button
                className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
                onClick={() => setActiveTab('dashboard')}
              >
                <LayoutDashboard size={14} /> Dashboard
              </button>
            )}

            <button
              className={`nav-tab ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <History size={14} /> History
            </button>

            <div className="nav-divider" />

            {stage !== 'input' && (
              <button className="btn-ghost" onClick={handleReset}>
                <RotateCcw size={14} /> New
              </button>
            )}
            <div className="user-chip">
              <User size={14} />
              <span>{user?.name || user?.email}</span>
            </div>
            <button className="btn-ghost" onClick={logout}>
              <LogOut size={14} /> Sign Out
            </button>
          </nav>
        </div>
      </header>

      {/* ── Stepper (only in analysis tab, after input) ── */}
      {activeTab === 'analysis' && stage !== 'input' && (
        <div className="stepper-bar"><WorkflowStepper stage={stage} /></div>
      )}

      <main className="app-main">

        {/* ══ HISTORY TAB ══ */}
        {activeTab === 'history' && <EmissionHistory />}

        {/* ══ DASHBOARD TAB ══ */}
        {activeTab === 'dashboard' && active && (
          <div className="dashboard-layout">
            {active.esg && <ESGScoreCard esg={active.esg} emissions={active.emission_result} />}
            <EmissionCharts emissions={active.emission_result} forecast={active.forecast} />
            {active.alerts && active.alerts.length > 0 && <AlertsPanel alerts={active.alerts} />}
            {active.simulations && active.simulations.length > 0 && <SimulationPanel simulations={active.simulations} />}
            {active.recommendations && active.recommendations.length > 0 && <RecommendationsPanel recommendations={active.recommendations} />}
            {active.traceability && active.traceability.length > 0 && <TraceabilityPanel items={active.traceability} />}
          </div>
        )}
        {activeTab === 'dashboard' && !active && (
          <div className="empty-dashboard">
            <LayoutDashboard size={40} style={{ color: 'var(--mid)', marginBottom: 12 }} />
            <p>No analysis yet. Run an analysis first to see your dashboard.</p>
            <button className="btn-primary" style={{ width: 'auto', marginTop: 12 }} onClick={() => setActiveTab('analysis')}>
              <PlusCircle size={16} /> Start Analysis
            </button>
          </div>
        )}

        {/* ══ ANALYSIS TAB ══ */}
        {activeTab === 'analysis' && (
          <>
            {/* INPUT */}
            {stage === 'input' && (
              <div className="landing">
                <div className="landing-hero">
                  <h2>Operational Carbon Intelligence</h2>
                  <p>
                    Upload invoices, utility bills, or operational data. Our AI extracts emissions,
                    validates data, and generates ESG insights — while identifying inefficiencies
                    that can be eliminated without reducing business output.
                  </p>
                  <div className="workflow-preview">
                    {['Upload', 'AI Extract', 'Validate', 'Review', 'ESG Report'].map((s, i, arr) => (
                      <React.Fragment key={s}>
                        <span>{s}</span>
                        {i < arr.length - 1 && <span className="arrow">→</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
                <div className="input-wrapper">
                  <InputSection onResult={handleExtracted} onExtracting={handleExtracting} />
                </div>
              </div>
            )}

            {/* EXTRACTING */}
            {stage === 'extracting' && (
              <div className="extracting-state">
                <div className="extracting-spinner" />
                <p className="extracting-text">AI is analyzing your document...</p>
                <p className="extracting-sub">Extracting emissions · Running ESG analysis · Generating insights</p>
              </div>
            )}

            {/* REVIEW */}
            {stage === 'review' && result && (
              <div className="review-layout">
                <div className="review-left">
                  <ValidationPanel validation={result.validation} confidenceScore={result.emission_result.confidence_score} />
                  <HITLReview extracted={result.extracted_data} validation={result.validation} onApproved={handleHITLUpdate} />
                </div>
                <div className="review-right">
                  <EmissionsResult result={result.emission_result} />
                  {result.alerts && result.alerts.length > 0 && <AlertsPanel alerts={result.alerts} />}
                </div>
              </div>
            )}

            {/* APPROVED */}
            {(stage === 'approved' || stage === 'report') && approvedResult && (
              <div className="approved-layout">
                {approvedResult.esg && (
                  <ESGScoreCard esg={approvedResult.esg} emissions={approvedResult.emission_result} />
                )}

                <div className="approved-row-2">
                  <EmissionsResult result={approvedResult.emission_result} />
                  <EmissionCharts emissions={approvedResult.emission_result} forecast={approvedResult.forecast} />
                </div>

                <div className="approved-row-3">
                  <div className="approved-col-left">
                    <ValidationPanel
                      validation={approvedResult.validation}
                      confidenceScore={approvedResult.emission_result.confidence_score}
                    />
                    <ReportSection
                      extractedData={approvedResult.extracted_data}
                      emissionResult={approvedResult.emission_result}
                      esgData={approvedResult.esg}
                      recommendations={approvedResult.recommendations}
                      forecast={approvedResult.forecast}
                    />
                  </div>
                  <div className="approved-col-right">
                    {approvedResult.alerts && approvedResult.alerts.length > 0 && (
                      <AlertsPanel alerts={approvedResult.alerts} />
                    )}
                    {approvedResult.simulations && approvedResult.simulations.length > 0 && (
                      <SimulationPanel simulations={approvedResult.simulations} />
                    )}
                  </div>
                </div>

                {approvedResult.recommendations && approvedResult.recommendations.length > 0 && (
                  <RecommendationsPanel recommendations={approvedResult.recommendations} />
                )}
                {approvedResult.traceability && approvedResult.traceability.length > 0 && (
                  <TraceabilityPanel items={approvedResult.traceability} />
                )}
              </div>
            )}
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>Carbon Intelligence v2 · IPCC/EPA/DEFRA emission factors · Human-in-the-loop validated · Enterprise ESG Platform</p>
      </footer>
    </div>
  );
}

export default function App() {
  return <AuthProvider><AppInner /></AuthProvider>;
}
