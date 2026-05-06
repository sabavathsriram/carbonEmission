import React, { useState } from 'react';
import { Leaf, Mail, Lock, User, Loader2, AlertCircle, Eye, EyeOff, Bell } from 'lucide-react';
import { loginUser, registerUser } from '../api';
import { useAuth } from '../contexts/AuthContext';

export default function AuthPage() {
  const { login } = useAuth();
  const [mode, setMode]       = useState<'login' | 'register'>('login');
  const [email, setEmail]     = useState('');
  const [password, setPassword] = useState('');
  const [name, setName]       = useState('');
  const [showPw, setShowPw]   = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = mode === 'login'
        ? await loginUser(email, password)
        : await registerUser(email, name, password);
      login(user);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => { setEmail('company@gmail.com'); setPassword('company@123'); };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <Leaf size={32} className="auth-logo-icon" />
          <div>
            <h1>Carbon Intelligence</h1>
            <p>Enterprise ESG &amp; Emissions Platform</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => setMode('login')}
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => setMode('register')}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <div className="auth-field">
              <label><User size={14} /> Full Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Jane Smith"
                required
              />
            </div>
          )}

          <div className="auth-field">
            <label><Mail size={14} /> Email Address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="company@gmail.com"
              required
            />
          </div>

          <div className="auth-field">
            <label><Lock size={14} /> Password</label>
            <div className="pw-wrap">
              <input
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'Create a password' : 'Enter password'}
                required
              />
              <button type="button" className="pw-toggle" onClick={() => setShowPw(p => !p)}>
                {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {/* SNS subscription note shown only on register */}
          {mode === 'register' && (
            <div className="auth-sns-note">
              <Bell size={13} />
              <span>
                After signing up, AWS will send a confirmation email to activate
                your notifications — emission summaries, spike alerts, and report confirmations.
                Click <strong>Confirm subscription</strong> in that email to enable alerts.
              </span>
            </div>
          )}

          {error && (
            <div className="error-banner">
              <AlertCircle size={15} /> {error}
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading
              ? <><Loader2 size={16} className="spin" /> {mode === 'login' ? 'Signing in...' : 'Creating account...'}</>
              : mode === 'login' ? 'Sign In' : 'Create Account'
            }
          </button>
        </form>

        {/* Demo credentials */}
        {mode === 'login' && (
          <div className="auth-demo">
            <p>Demo credentials:</p>
            <button className="demo-fill-btn" onClick={fillDemo}>
              Use demo account (company@gmail.com)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
