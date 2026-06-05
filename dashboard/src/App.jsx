import React, { useState } from 'react';
import './App.css';

const API = 'http://127.0.0.1:5000';

// ── helpers ──────────────────────────────────
const fmt = (n) => typeof n === 'number' ? `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—';
const fmtN = (n) => typeof n === 'number' ? n.toFixed(1) : '—';

// ── Sub-components ────────────────────────────

function NiftyBanner({ data }) {
  if (!data) return null;
  const bullish = data.trend === 'BULLISH';
  const mixed   = data.trend === 'MIXED';
  const color   = bullish ? '#00e5a0' : mixed ? '#f5c842' : '#f56060';
  return (
    <div className="nifty-banner">
      <div className="nifty-left">
        <span className="nifty-label">NIFTY 50</span>
        <span className="nifty-price">{fmt(data.price)}</span>
        <span className="nifty-chg" style={{ color: data.pct >= 0 ? '#00e5a0' : '#f56060' }}>
          {data.pct >= 0 ? '▲' : '▼'} {Math.abs(data.pct)}%
        </span>
      </div>
      <div className="nifty-pills">
        <Pill label={`20 EMA ${fmt(data.ema20)}`} ok={data.price > data.ema20} />
        <Pill label={`50 EMA ${fmt(data.ema50)}`} ok={data.above50} />
        <Pill label={`200 EMA ${fmt(data.ema200)}`} ok={data.above200} />
      </div>
      <div className="nifty-regime" style={{ color }}>
        {bullish ? '📈' : mixed ? '↔️' : '📉'} Market: <strong>{data.trend}</strong>
        <span className="nifty-note">
          {bullish
            ? ' — Ideal for pullback buys. Trend is your friend.'
            : mixed
            ? ' — Be selective. Only high-quality setups.'
            : ' — Caution: avoid aggressive longs.'}
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
        {score >= 8 ? 'HIGH CONVICTION' : score >= 6.5 ? 'GOOD SETUP' : 'WATCHLIST'}
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
          <div className="ps-label">Pullback</div>
          <div className="ps-val pullback">{pick.pullback_pct}%</div>
        </div>
        <div>
          <div className="ps-label">Support</div>
          <div className="ps-val support">{fmt(pick.support_level)}</div>
        </div>
        <div>
          <div className="ps-label">RSI</div>
          <div className="ps-val rsi">{fmtN(pick.rsi)}</div>
        </div>
        <div>
          <div className="ps-label">Vol Ratio</div>
          <div className="ps-val" style={{ color: pick.vol_expanding ? '#00e5a0' : '#f5c842' }}>{pick.vol_ratio}×</div>
        </div>
      </div>

      {/* Signal chips */}
      <div className="chips-row">
        <span className="chip green">▲ Uptrend</span>
        <span className="chip yellow">↓ {pick.pullback_pct}% Pullback</span>
        <span className="chip blue">{pick.support_name} Support</span>
        {pick.candle && pick.candle !== 'No clear pattern yet' && <span className="chip purple">{pick.candle}</span>}
        {pick.vol_dry_up && <span className="chip grey">Vol Dry-Up</span>}
        {pick.vol_expanding && <span className="chip green">Vol Expanding</span>}
      </div>

      {/* Thesis */}
      <div className="thesis-box">
        <div className="thesis-label">Technical Thesis</div>
        <p className="thesis-text">{pick.thesis}</p>
      </div>

      {/* Trade levels */}
      <div className="levels-grid">
        <div className="level-item entry">
          <div className="li-label">ENTRY</div>
          <div className="li-val">{fmt(pick.entry)}</div>
        </div>
        <div className="level-item sl">
          <div className="li-label">STOP LOSS</div>
          <div className="li-val">{fmt(pick.stop_loss)}</div>
          <div className="li-sub">{riskPct}% risk</div>
        </div>
        <div className="level-item t1">
          <div className="li-label">TARGET 1</div>
          <div className="li-val">{fmt(pick.t1)}</div>
        </div>
        <div className="level-item t2">
          <div className="li-label">TARGET 2</div>
          <div className="li-val">{fmt(pick.t2)}</div>
        </div>
        <div className="level-item rr">
          <div className="li-label">RISK : REWARD</div>
          <div className="li-val rr-val">1 : {pick.rr}</div>
        </div>
      </div>

      {/* Entry strategy accordion */}
      <button className="toggle-btn" onClick={() => setOpen(o => !o)}>
        {open ? '▲ Hide' : '▼ Show'} Entry Strategy
      </button>
      {open && (
        <div className="entry-strategy">
          <div className="es-label">Ideal Entry Strategy</div>
          <p className="es-text">{pick.entry_strategy}</p>
          <div className="ema-row">
            <span>20 EMA: {fmt(pick.ema20)}</span>
            <span>50 EMA: {fmt(pick.ema50)}</span>
            <span>200 EMA: {fmt(pick.ema200)}</span>
            <span>Recent High: {fmt(pick.recent_high)}</span>
          </div>
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
        <circle cx="24" cy="24" r="20" fill="none" stroke="#00e5a0" strokeWidth="4"
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
              <div className="hdr-badge">ELITE PULLBACK SCANNER</div>
              <h1>NSE Swing Trade Radar</h1>
              <p className="hdr-sub">
                Nifty 500 + F&amp;O Universe · Real-time yfinance data · Run fresh every day
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
                  Scanning…
                </>
              ) : (
                <>⚡ Run Today's Scan</>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        {/* Idle state */}
        {state === 'idle' && (
          <div className="empty-state">
            <div className="empty-icon">📡</div>
            <h2>Ready to Scan</h2>
            <p>Click <strong>Run Today's Scan</strong> above to find today's top 3 pullback reversal setups from the Nifty 500 universe using live market data.</p>
            <div className="empty-criteria">
              <div className="ec-item">
                <span className="ec-icon">📈</span>
                <span>Stock above 50 EMA + 200 EMA (confirmed uptrend)</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">↘️</span>
                <span>2.5–10% pullback from recent high</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">🎯</span>
                <span>Retesting 20 EMA, 50 EMA, or breakout level</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">🕯️</span>
                <span>Bullish reversal candle (Hammer / Engulfing)</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">📊</span>
                <span>Volume drying on dip, expanding on reversal</span>
              </div>
              <div className="ec-item">
                <span className="ec-icon">📉</span>
                <span>RSI cooled to 40–62 buy zone</span>
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
            <h2>Scanning {91} Stocks Live…</h2>
            <p>Fetching real-time data from Yahoo Finance and running Elite Pullback criteria across the Nifty 500 / F&amp;O universe.</p>
            <div className="progress-steps">
              <div className="ps-step active">Fetching OHLCV Data</div>
              <div className="ps-step active">Calculating EMAs &amp; RSI</div>
              <div className="ps-step active">Detecting Reversals</div>
              <div className="ps-step active">Scoring &amp; Ranking</div>
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
            <p>Then click <strong>Run Today's Scan</strong> again.</p>
            <button className="scan-btn" onClick={runScan}>Retry</button>
          </div>
        )}

        {/* Results */}
        {state === 'done' && data && (
          <>
            <NiftyBanner data={data.nifty50} />

            <div className="scan-meta">
              <span>🕐 Scanned: {data.scan_time}</span>
              <span>📊 Stocks Scanned: {data.scanned}</span>
              <span>✅ Valid Setups Found: {data.found}</span>
              <span>⚡ Time: {data.elapsed}s</span>
            </div>

            {data.picks.length === 0 ? (
              <div className="no-picks">
                <div className="no-picks-icon">🔍</div>
                <h2>No High-Quality Setups Today</h2>
                <p>The scanner found no stocks meeting all Elite Pullback criteria right now. Check back later in the session or after a market pullback creates fresh entry opportunities.</p>
              </div>
            ) : (
              <>
                <div className="picks-header">
                  <h2>Top {data.picks.length} Elite Pullback Setups</h2>
                  <p>Filtered from {data.found} valid setups · Ranked by conviction score · Sector-diversified</p>
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
        <p>For educational purposes only. Not financial advice. Always use stop losses.</p>
      </footer>
    </div>
  );
}
