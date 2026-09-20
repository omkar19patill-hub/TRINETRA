import { useState, useEffect } from 'react'

interface BackendStatus {
  online: boolean
  data?: any
  error?: string
}

export default function App() {
  const [status, setStatus] = useState<BackendStatus>({ online: false })
  const [loading, setLoading] = useState(true)
  const [pingResult, setPingResult] = useState<any>(null)
  const [pinging, setPinging] = useState(false)

  const checkBackend = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatus({ online: true, data })
    } catch (err: any) {
      // Fallback relative path proxy check
      try {
        const resProxy = await fetch('/orchestration/health')
        if (resProxy.ok) {
          const data = await resProxy.json()
          setStatus({ online: true, data })
          return
        }
      } catch (_) {}
      setStatus({
        online: false,
        error: err?.message || 'Cannot reach FastAPI backend at http://localhost:8000',
      })
    } finally {
      setLoading(false)
    }
  }

  const pingEndpoint = async (path: string) => {
    setPinging(true)
    try {
      const url = path.startsWith('http') ? path : `http://localhost:8000${path}`
      const res = await fetch(url)
      const data = await res.json()
      setPingResult({ path, status: res.status, data })
    } catch (err: any) {
      setPingResult({ path, error: err?.message || 'Request failed' })
    } finally {
      setPinging(false)
    }
  }

  useEffect(() => {
    checkBackend()
  }, [])

  const modules = [
    { name: 'Threat Intelligence Ingestion', badge: 'Live', endpoint: '/ingestion/health', desc: 'NVD 2.0, FIRST EPSS, CISA KEV & MITRE ATT&CK integration' },
    { name: 'Deterministic Risk Scoring', badge: 'Active', endpoint: '/risk/health', desc: 'CVSS, EPSS, KEV & exposure factor deterministic calculation' },
    { name: 'Financial Cyber Risk (CRQ)', badge: 'Open FAIR', endpoint: '/financial-crq/health', desc: 'Downtime loss, total loss magnitude & Expected Annual Loss' },
    { name: 'Monte Carlo Stochastic Engine', badge: '100k Iter', endpoint: '/monte-carlo/health', desc: 'Triangular distribution uncertainty & percentiles (P50-P99)' },
    { name: 'Decision Intelligence', badge: 'DEV 2', endpoint: '/decision/health', desc: 'Alternative portfolios, opportunity cost & marginal budget' },
    { name: 'ML Risk Calibration', badge: 'XGBoost', endpoint: '/ml/health', desc: 'Empirical risk calibration & incident probability modeling' },
    { name: 'Explainable AI', badge: 'RAG Grounded', endpoint: '/ai/health', desc: 'Zero-hallucination executive narratives & decision evidence' },
    { name: 'Blockchain Provenance & Re-Opt', badge: 'Immutable', endpoint: '/blockchain/health', desc: 'Tamper-evident ledger receipts & continuous re-optimization' },
  ]

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '40px 20px' }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #38bdf8, #3b82f6)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            fontWeight: 800,
            color: '#070d18',
            boxShadow: '0 0 25px rgba(56, 189, 248, 0.4)'
          }}>
            T
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #f8fafc, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              TRINETRA &middot; Frontend Platform
            </h1>
            <p style={{ fontSize: '13px', color: '#94a3b8' }}>
              AI-Powered Continuous Cyber Risk Quantification & Investment Optimization &middot; SIH 2026 (SIH26105)
            </p>
          </div>
        </div>

        {/* Status Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '9999px',
          padding: '8px 18px',
          fontSize: '13px',
          fontFamily: 'JetBrains Mono, monospace'
        }}>
          <span style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: loading ? '#f59e0b' : status.online ? '#10b981' : '#f43f5e',
            boxShadow: `0 0 10px ${loading ? '#f59e0b' : status.online ? '#10b981' : '#f43f5e'}`
          }} />
          <span>
            {loading ? 'Probing Backend...' : status.online ? 'FastAPI Connected (Port 8000)' : 'Backend Offline'}
          </span>
          <button
            onClick={checkBackend}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#38bdf8',
              cursor: 'pointer',
              marginLeft: '8px',
              textDecoration: 'underline',
              fontSize: '12px'
            }}
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Hero Card */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.7)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        borderRadius: '16px',
        padding: '28px',
        marginBottom: '32px',
        backdropFilter: 'blur(12px)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <span style={{
              fontSize: '11px',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              color: '#38bdf8',
              fontWeight: 700,
              background: 'rgba(56, 189, 248, 0.12)',
              padding: '4px 10px',
              borderRadius: '6px'
            }}>
              Frontend Verified &middot; Vite 5 + React 18 + TypeScript
            </span>
            <h2 style={{ fontSize: '20px', fontWeight: 700, marginTop: '12px', marginBottom: '8px' }}>
              Cyber Risk Engine Client Ready
            </h2>
            <p style={{ fontSize: '14px', color: '#94a3b8', maxWidth: '640px' }}>
              The frontend environment is fully initialized and operational. It communicates with the unified TRINETRA Python backend serving Cyber Threat Intelligence Ingestion, Deterministic Risk, Open FAIR CRQ, Monte Carlo, Decision Optimization, and Blockchain Provenance.
            </p>
          </div>
          <div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'inline-block',
                background: 'linear-gradient(135deg, #38bdf8, #3b82f6)',
                color: '#070d18',
                fontWeight: 700,
                fontSize: '13px',
                padding: '12px 20px',
                borderRadius: '10px',
                textDecoration: 'none',
                boxShadow: '0 0 20px rgba(56, 189, 248, 0.35)'
              }}
            >
              Open Backend Swagger Docs &rarr;
            </a>
          </div>
        </div>
      </div>

      {/* Modules Grid */}
      <h3 style={{ fontSize: '16px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '16px' }}>
        Engine Subsystems & Quick Health Checks
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        {modules.map((m) => (
          <div
            key={m.name}
            style={{
              background: 'rgba(15, 23, 42, 0.65)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '12px',
              padding: '18px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'border-color 0.2s',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px' }}>
                  {m.badge}
                </span>
                <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'JetBrains Mono, monospace' }}>
                  {m.endpoint}
                </span>
              </div>
              <h4 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>{m.name}</h4>
              <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>{m.desc}</p>
            </div>
            <button
              onClick={() => pingEndpoint(m.endpoint)}
              disabled={pinging}
              style={{
                marginTop: '14px',
                background: pinging ? 'rgba(255, 255, 255, 0.02)' : 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: pinging ? '#64748b' : '#f8fafc',
                borderRadius: '6px',
                padding: '6px 12px',
                fontSize: '12px',
                cursor: pinging ? 'not-allowed' : 'pointer',
                textAlign: 'center',
                fontFamily: 'JetBrains Mono, monospace'
              }}
            >
              {pinging ? 'Pinging...' : 'Ping Health →'}
            </button>
          </div>
        ))}
      </div>

      {/* Live Probe Result Window */}
      {pingResult && (
        <div style={{
          background: 'rgba(3, 7, 18, 0.85)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '32px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: '#38bdf8', fontFamily: 'JetBrains Mono, monospace' }}>
              📡 Live Response for {pingResult.path} (HTTP {pingResult.status || 'ERR'})
            </span>
            <button
              onClick={() => setPingResult(null)}
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '13px' }}
            >
              ✕ Close
            </button>
          </div>
          <pre style={{
            fontSize: '12px',
            color: '#cbd5e1',
            background: '#070d18',
            padding: '14px',
            borderRadius: '8px',
            overflowX: 'auto',
            border: '1px solid rgba(255,255,255,0.05)'
          }}>
            {JSON.stringify(pingResult.data || pingResult.error, null, 2)}
          </pre>
        </div>
      )}

      {/* Footer */}
      <footer style={{ textAlign: 'center', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '20px', color: '#64748b', fontSize: '12px' }}>
        TRINETRA Cyber Risk Quantification & Investment Optimization Platform &middot; DEV 2 Unified Frontend Setup
      </footer>
    </div>
  )
}
