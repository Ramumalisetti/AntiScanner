import React, { useState } from 'react';
import './App.css';

const API = 'http://127.0.0.1:5000';

// ── helpers ──────────────────────────────────
const fmt = (n) => typeof n === 'number' ? `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—';
const fmtN = (n) => typeof n === 'number' ? n.toFixed(1) : '—';

// ── Sub-components ────────────────────────────

function NiftyBanner({ data }) {
  if (!data) return null;
  const bullish = data.structure === 'BULLISH BOS';
  const bearish = data.structure === 'BEARISH CHOCH';
  const mixed   = data.structure === 'CONSOLIDATION';
  const color   = bullish ? '#00e5a0' : mixed ? '#f5c842' : '#f56060';
  return (
    <div className="nifty-banner">
      <div className="nifty-left">
        <span className="nifty-label">NIFTY 50 LQM</span>
        <span className="nifty-price">{fmt(data.price)}</span>
        <span className="nifty-chg" style={{ color: data.pct >= 0 ? '#00e5a0' : '#f56060' }}>
          {data.pct >= 0 ? '▲' : '▼'} {Math.abs(data.pct)}%
        </span>
      </div>
      <div className="nifty-pills">
        <Pill label={`Structure: ${data.structure}`} ok={bullish} />
        <Pill label={data.premium ? 'Premium Pricing' : 'Discount Pricing'} ok={!data.premium} />
      </div>
      <div className="nifty-regime" style={{ color }}>
        {bullish ? '📈' : mixed ? '↔️' : '📉'} Context: <strong>{data.structure}</strong>
        <span className="nifty-note">
          {bullish
            ? ' — Ideal conditions for Long Demand OB / FVG entries.'
            : mixed
            ? ' — Range-bound. Look for liquidity sweeps.'
            : ' — High Risk. Institutional distribution active.'}
        </span>
      </div>
    </div>
  );
}

function Pill({ label, ok }) {
  return (
    <span className="pill" style={{ background: ok ? 'rgba(0,229,160,.12)' : 'rgba(245,96,96,.12)', color: ok ? '#00e5a0' : '#f56060', border: `1px solid ${ok ? 'rgba(0,229,160,.3)' : 'rgba(245,96,96,.3)'}` }}>
      {ok ? '✓' : '✗'} {label}
    </span>
  );
}

function ScoreRing({ score }) {
  const pct  = (score / 10) * 100;
  const c    = score >= 8 ? '#00e5a0' : score >= 6.5 ? '#f5c842' : '#f97316';
  const r    = 30;
  const circ = 2 * Math.PI * r;
  const dash = circ * (pct / 100);
  return (
    <div className="score-ring-wrap">
      <svg width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="7" />
        <circle cx="40" cy="40" r={r} fill="none" stroke={c} strokeWidth="7"
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeDashoffset={circ / 4}
          strokeLinecap="round" />
        <text x="40" y="38" textAnchor="middle" fill={c} fontSize="14" fontWeight="900" fontFamily="'JetBrains Mono',monospace">{score}</text>
        <text x="40" y="52" textAnchor="middle" fill="rgba(255,255,255,.4)" fontSize="8" fontFamily="'JetBrains Mono',monospace">/10</text>
      </svg>
      <span className="score-label" style={{ color: c }}>
        {score >= 8 ? 'A+ SMC SETUP' : score >= 6.5 ? 'A- GRADE' : 'B GRADE'}
      </span>
    </div>
  );
}

function TradeCard({ pick, rank }) {
  const [open, setOpen] = useState(false);
  const badges = { 1: '🥇', 2: '🥈', 3: '🥉' };
  const riskPct = pick.price > 0 ? ((pick.entry - pick.stop_loss) / pick.entry * 100).toFixed(1) : 0;

  return (
    <div className={`trade-card rank-${rank}`}>
      {/* Header */}
      <div className="card-head">
        <div className="card-head-left">
          <span className="rank-badge">{badges[rank] || `#${rank}`}</span>
          <div>
            <h2 className="sym">{pick.sym}</h2>
            <span className="sector-tag">{pick.sector}</span>
          </div>
        </div>
        <ScoreRing score={pick.score} />
      </div>

      {/* Price strip */}
      <div className="price-strip">
        <div>
          <div className="ps-label">CMP</div>
          <div className="ps-val">{fmt(pick.price)}</div>
        </div>
        <div>
          <div className="ps-label">Discount Pullback</div>
          <div className="ps-val pullback">{pick.pullback_pct}%</div>
        </div>
        <div>
          <div className="ps-label">Mitigation Zone</div>
          <div className="ps-val support">{fmt(pick.support_level)}</div>
        </div>
        <div>
          <div className="ps-label">Vol Ratio</div>
          <div className="ps-val" style={{ color: pick.vol_ratio > 1.2 ? '#00e5a0' : '#f5c842' }}>{pick.vol_ratio}×</div>
        </div>
      </div>

      {/* Signal chips */}
      <div className="chips-row">
        {pick.ob_active && <span className="chip green">🧱 Demand OB Tapped</span>}
        {pick.fvg_active && <span className="chip blue">🧲 FVG Mitigated</span>}
        {pick.liq_sweep && <span className="chip purple">🚨 Liquidity Swept</span>}
        {(!pick.ob_active && !pick.fvg_active && !pick.liq_sweep) && <span className="chip grey">Pending Structure</span>}
      </div>

      {/* Thesis */}
      <div className="thesis-box">
        <div className="thesis-label">Institutional Thesis</div>
        <p className="thesis-text">{pick.thesis}</p>
      </div>

      {/* Trade levels */}
      <div className="levels-grid">
        <div className="level-item entry">
          <div className="li-label">ENTRY ZONE</div>
          <div className="li-val">{fmt(pick.entry)}</div>
        </div>
        <div className="level-item sl">
          <div className="li-label">STOP LOSS (Sweep/OB)</div>
          <div className="li-val">{fmt(pick.stop_loss)}</div>
          <div className="li-sub">{riskPct}% risk</div>
        </div>
        <div className="level-item t1">
          <div className="li-label">LIQUIDITY TARGET 1</div>
          <div className="li-val">{fmt(pick.t1)}</div>
        </div>
        <div className="level-item t2">
          <div className="li-label">STRUCTURAL HIGH</div>
          <div className="li-val">{fmt(pick.t2)}</div>
        </div>
        <div className="level-item rr">
          <div className="li-label">ASYMMETRY (R:R)</div>
          <div className="li-val rr-val">1 : {pick.rr}</div>
        </div>
      </div>

      {/* Entry strategy accordion */}
      <button className="toggle-btn" onClick={() => setOpen(o => !o)}>
        {open ? '▲ Hide' : '▼ Show'} Execution Strategy
      </button>
      {open && (
        <div className="entry-strategy">
          <div className="es-label">Execution Rules</div>
          <p className="es-text">{pick.entry_strategy}</p>
        </div>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <div className="spinner-wrap">
      <svg className="spin" width="48" height="48" viewBox="0 0 48 48">
        <circle cx="24" cy="24" r="20" fill="none" stroke="rgba(255,255,255,.1)" strokeWidth="4" />
        <circle cx="24" cy="24" r="20" fill="none" stroke="#9d7cfc" strokeWidth="4"
          strokeDasharray="40 88" strokeLinecap="round" />
      </svg>
    </div>
  );
}

// ── Main App ─────────────────────────────────
export default function App() {
  const [state, setState] = useState('idle'); // idle | loading | done | error
  const [data,  setData]  = useState(null);
  const [err,   setErr]   = useState('');

  const runScan = async () => {
    setState('loading');
    setErr('');
    try {
      const res  = await fetch(`${API}/api/scan`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setState('done');
    } catch (e) {
      setErr(e.message.includes('Failed to fetch')
        ? 'Cannot connect to API. Make sure the Python backend is running:\n  python api.py'
        : e.message);
      setState('error');
    }
  };

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="hdr">
        <div className="hdr-inner">
          <div className="hdr-top">
            <div>
              <div className="hdr-badge">PURE INSTITUTIONAL SMC SCANNER</div>
              <h1>NSE Smart Money Radar</h1>
              <p className="hdr-sub">
                Hunting Liquidity Sweeps, Order Blocks, and Fair Value Gaps in the Nifty 500
              </p>
            </div>
            <button
              className={`scan-btn ${state === 'loading' ? 'scanning' : ''}`}
              onClick={runScan}
              disabled={state === 'loading'}
            >
              {state === 'loading' ? (
                <>
                  <svg className="spin" width="18" height="18" viewBox="0 0 18 18">
                    <circle cx="9" cy="9" r="7" fill="none" stroke="#000" strokeWidth="2.5" strokeDasharray="15 30" strokeLinecap="round" />
                  </svg>
                  Hunting Footprints…
                </>
              ) : (
                <>⚡ Scan Smart Money</>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        {/* Idle state */}
        {state === 'idle' && (
          <div className="empty-state">
            <div className="empty-icon">🏦</div>
            <h2>Ready to Hunt Institutional Liquidity</h2>
            <p>Click <strong>Scan Smart Money</strong> above to analyze the Nifty 500 for A+ institutional setups.</p>
            <div className="empty-criteria">
              <div className="ec-item">
                <span className="ec-icon">🧱</span>
                <span>Demand Order Block (OB) Taps</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">🧲</span>
                <span>Fair Value Gap (FVG) Mitigations</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">🚨</span>
                <span>Stop Hunts / Liquidity Sweeps</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">📈</span>
                <span>Break of Structure (BOS) Confirmation</span>
              </div>
            </div>
            <div className="api-tip">
              <strong>Tip:</strong> The Python backend must be running for live data.
              Start it with: <code>python api.py</code>
            </div>
          </div>
        )}

        {/* Loading */}
        {state === 'loading' && (
          <div className="loading-state">
            <Spinner />
            <h2>Scanning 500 Stocks for SMC Footprints…</h2>
            <p>Scanning the entire Nifty 500 universe for Order Blocks, Fair Value Gaps, and Liquidity Sweeps.</p>
            <div className="progress-steps">
              <div className="ps-step active">Parsing Order Flow</div>
              <div className="ps-step active">Identifying FVGs</div>
              <div className="ps-step active">Mapping Liquidity</div>
              <div className="ps-step active">Calculating Asymmetry</div>
            </div>
          </div>
        )}

        {/* Error */}
        {state === 'error' && (
          <div className="error-state">
            <div className="error-icon">⚠️</div>
            <h2>Connection Failed</h2>
            <pre className="error-msg">{err}</pre>
            <p>Open a terminal in <code>c:\Work\Scanners</code> and run:</p>
            <pre className="code-block">python api.py</pre>
            <p>Then click <strong>Scan Smart Money</strong> again.</p>
            <button className="scan-btn" onClick={runScan}>Retry</button>
          </div>
        )}

        {/* Results */}
        {state === 'done' && data && (
          <>
            <NiftyBanner data={data.nifty50} />

            <div className="scan-meta">
              <span>🕐 Scan Time: {data.scan_time}</span>
              <span>📊 Tickers Processed: {data.scanned}</span>
              <span>✅ A+ SMC Setups Found: {data.found}</span>
              <span>⚡ Processing Speed: {data.elapsed}s</span>
            </div>

            {data.picks.length === 0 ? (
              <div className="no-picks">
                <div className="no-picks-icon">📉</div>
                <h2>No A+ SMC Setups Today</h2>
                <p>No clean Order Blocks, FVGs, or Liquidity Sweeps detected right now. The Smart Money is quiet.</p>
              </div>
            ) : (
              <>
                <div className="picks-header">
                  <h2>Top Institutional SMC Setups</h2>
                  <p>Filtered from {data.found} valid setups · Ranked by SMC Confluence</p>
                </div>
                <div className="cards-grid">
                  {data.picks.map((pick, i) => (
                    <TradeCard key={pick.sym} pick={pick} rank={i + 1} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <p>For educational purposes only. Pure Smart Money Concepts. Always use strict structural stop losses.</p>
      </footer>
    </div>
  );
}
