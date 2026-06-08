import React, { useState } from 'react';
import './App.css';

const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:5000'
  : window.location.origin;

const fmt = (n) => typeof n === 'number' ? `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—';

function NiftyBanner({ data }) {
  if (!data) return null;
  const ok = data.status === 'BULL MARKET';
  return (
    <div className="nifty-banner">
      <div className="nifty-left">
        <span className="nifty-label">NIFTY 50 TREND</span>
        <span className="nifty-price">{fmt(data.price)}</span>
        <span className="nifty-chg" style={{ color: data.pct >= 0 ? '#00e5a0' : '#f56060' }}>
          {data.pct >= 0 ? '▲' : '▼'} {Math.abs(data.pct)}%
        </span>
      </div>
      <div className="nifty-pills">
        <span className="pill" style={{ background: ok ? 'rgba(0,229,160,.12)' : 'rgba(245,96,96,.12)', color: ok ? '#00e5a0' : '#f56060', border: `1px solid ${ok ? 'rgba(0,229,160,.3)' : 'rgba(245,96,96,.3)'}` }}>
          {ok ? '✓' : '✗'} {data.status}
        </span>
      </div>
    </div>
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
      <span className="score-label" style={{ color: c }}>High Prob Bounce</span>
    </div>
  );
}

function TradeCard({ pick, rank }) {
  const badges = { 1: '🥇', 2: '🥈', 3: '🥉' };
  const riskPct = pick.price > 0 ? ((pick.entry - pick.stop_loss) / pick.entry * 100).toFixed(1) : 0;

  return (
    <div className={`trade-card rank-${rank}`}>
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

      <div className="price-strip">
        <div>
          <div className="ps-label">CMP</div>
          <div className="ps-val">{fmt(pick.price)}</div>
        </div>
        <div>
          <div className="ps-label">Oversold RSI</div>
          <div className="ps-val" style={{color: pick.rsi < 35 ? '#00e5a0' : '#f5c842'}}>{pick.rsi}</div>
        </div>
        <div>
          <div className="ps-label">Uptrend 200 EMA</div>
          <div className="ps-val" style={{color: pick.price > pick.ema200 ? '#00e5a0' : '#f56060'}}>{fmt(pick.ema200)}</div>
        </div>
        <div>
          <div className="ps-label">Volatile ATR</div>
          <div className="ps-val">₹{pick.atr}</div>
        </div>
      </div>

      <div className="chips-row">
        <span className="chip green">📈 &gt;200 EMA Uptrend</span>
        <span className="chip blue">📉 Oversold RSI &lt; 40</span>
        {pick.ob_active && <span className="chip purple">🧱 Demand Zone</span>}
      </div>

      <div className="thesis-box">
        <div className="thesis-label">Mean Reversion Thesis</div>
        <p className="thesis-text">{pick.thesis}</p>
      </div>

      <div className="levels-grid">
        <div className="level-item entry">
          <div className="li-label">ENTRY</div>
          <div className="li-val">{fmt(pick.entry)}</div>
        </div>
        <div className="level-item sl">
          <div className="li-label">WIDE STOP LOSS (2x ATR)</div>
          <div className="li-val">{fmt(pick.stop_loss)}</div>
          <div className="li-sub">{riskPct}% room to breathe</div>
        </div>
        <div className="level-item t1">
          <div className="li-label">TARGET 1 (Reversion)</div>
          <div className="li-val">{fmt(pick.t1)}</div>
        </div>
        <div className="level-item rr">
          <div className="li-label">HIGH-WIN R:R</div>
          <div className="li-val rr-val">1 : {pick.rr}</div>
        </div>
      </div>
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

function HistoryItem({ record }) {
  const [open, setOpen] = useState(false);
  
  return (
    <div className={`history-item ${open ? 'open' : ''}`}>
      <div className="history-item-header" onClick={() => setOpen(!open)}>
        <div className="history-header-left">
          <span className="history-icon">📅</span>
          <span className="history-time">{record.scan_time}</span>
        </div>
        <div className="history-header-right">
          <span className="history-count-badge">{record.picks.length} picks</span>
          <span className="history-arrow">{open ? '▲' : '▼'}</span>
        </div>
      </div>
      
      {open && (
        <div className="history-item-body">
          <div className="history-picks-list">
            {record.picks.map((pick) => (
              <div key={pick.sym} className="history-pick-row">
                <div className="history-pick-header">
                  <div className="history-pick-left">
                    <span className="h-sym">{pick.sym}</span>
                    <span className="h-sector">{pick.sector}</span>
                  </div>
                  <span className="h-score">Score: {pick.score}/10</span>
                </div>
                <div className="history-pick-details">
                  <span>Price: <strong>{fmt(pick.price)}</strong></span>
                  <span>RSI: <strong style={{color: pick.rsi < 35 ? '#00e5a0' : '#f5c842'}}>{pick.rsi}</strong></span>
                  <span>Entry: <strong style={{color: '#00e5a0'}}>{fmt(pick.entry)}</strong></span>
                  <span>SL: <strong style={{color: '#f56060'}}>{fmt(pick.stop_loss)}</strong></span>
                  <span>Target (5%): <strong style={{color: '#6ee7b7'}}>{fmt(pick.t1)}</strong></span>
                </div>
                <div className="history-pick-thesis">
                  <p>{pick.thesis}</p>
                </div>
              </div>
            ))}
          </div>

          {(record.priyank_pick || record.darvax_pick) && (
            <div className="history-analyst-section" style={{marginTop: '20px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '15px'}}>
              <h4 style={{fontSize: '0.9rem', color: '#fff', marginBottom: '10px'}}>⚡ Featured Analyst Picks</h4>
              <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                {record.priyank_pick && (
                  <div className="history-analyst-row">
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px'}}>
                      <span style={{fontSize: '0.82rem'}}>🙋‍♂️ <strong>Priyank Sharma:</strong> <strong style={{color: '#fff'}}>{record.priyank_pick.sym}</strong> ({record.priyank_pick.sector})</span>
                      <span className="history-count-badge" style={{background: 'rgba(59,130,246,0.1)', color: '#3b82f6', borderColor: 'rgba(59,130,246,0.2)'}}>Score: {record.priyank_pick.score}</span>
                    </div>
                    <div className="history-pick-details">
                      <span>Price: <strong>{fmt(record.priyank_pick.price)}</strong></span>
                      <span>Entry: <strong>{fmt(record.priyank_pick.trade?.entry)}</strong></span>
                      <span>SL: <strong>{fmt(record.priyank_pick.trade?.sl)}</strong></span>
                      <span>T2 Target: <strong>{fmt(record.priyank_pick.trade?.t2)}</strong></span>
                    </div>
                  </div>
                )}
                {record.darvax_pick && (
                  <div className="history-analyst-row">
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px'}}>
                      <span style={{fontSize: '0.82rem'}}>📈 <strong>AmitabhJha3:</strong> <strong style={{color: '#fff'}}>{record.darvax_pick.sym}</strong> ({record.darvax_pick.sector})</span>
                      <span className="history-count-badge" style={{background: 'rgba(157,124,252,0.1)', color: '#9d7cfc', borderColor: 'rgba(157,124,252,0.2)'}}>Grade {record.darvax_pick.grade} ({record.darvax_pick.score})</span>
                    </div>
                    <div className="history-pick-details">
                      <span>Price: <strong>{fmt(record.darvax_pick.price)}</strong></span>
                      <span>Entry: <strong>{fmt(record.darvax_pick.trade?.entry)}</strong></span>
                      <span>SL: <strong>{fmt(record.darvax_pick.trade?.sl)}</strong></span>
                      <span>T2 Target: <strong>{fmt(record.darvax_pick.trade?.t2)}</strong></span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function HistorySection({ historyData, onClear }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="history-section">
      <div className="history-section-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>📜 Scan History Logs ({historyData.length})</h3>
        <div className="history-section-actions" onClick={(e) => e.stopPropagation()}>
          {historyData.length > 0 && (
            <button className="clear-hist-btn" onClick={onClear}>Clear Logs</button>
          )}
          <span className="expand-toggle" style={{cursor: 'pointer', marginLeft: '10px'}} onClick={() => setIsExpanded(!isExpanded)}>
            {isExpanded ? '▲' : '▼'}
          </span>
        </div>
      </div>
      
      {isExpanded && (
        <div className="history-list">
          {historyData.length === 0 ? (
            <div className="history-empty-msg">
              No history recorded yet. Run a scan to save results.
            </div>
          ) : (
            historyData.map((record, i) => (
              <HistoryItem key={record.scan_time + i} record={record} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

function AnalystTradeCard({ pick, analystName, badgeText, colorClass }) {
  const t = pick.trade || {};
  const isPriyank = analystName === "Priyank Sharma";
  const signals = pick.signals || [];
  
  return (
    <div className={`trade-card analyst-card ${colorClass}`}>
      <div className="card-head">
        <div className="card-head-left">
          <span className="rank-badge" style={{fontSize: '1.2rem'}}>{isPriyank ? '🙋‍♂️' : '📈'}</span>
          <div>
            <h2 className="sym">{pick.sym}</h2>
            <span className="sector-tag">{pick.sector}</span>
          </div>
        </div>
        <div className="score-ring-wrap" style={{alignItems: 'flex-end'}}>
          <div className="analyst-badge-pill" style={{
            fontSize: '0.62rem',
            background: isPriyank ? 'rgba(59,130,246,0.12)' : 'rgba(157,124,252,0.12)',
            color: isPriyank ? '#3b82f6' : '#9d7cfc',
            border: `1px solid ${isPriyank ? 'rgba(59,130,246,0.3)' : 'rgba(157,124,252,0.3)'}`,
            padding: '2px 8px',
            borderRadius: '4px',
            fontWeight: 'bold',
            fontFamily: 'var(--mono)'
          }}>{badgeText}</div>
          <span className="score-label" style={{ color: isPriyank ? '#3b82f6' : '#9d7cfc', fontSize: '0.75rem', marginTop: '4px', fontWeight: 'bold' }}>
            {isPriyank ? `Score: ${pick.score}/100` : `Grade ${pick.grade} (${pick.score}/100)`}
          </span>
        </div>
      </div>

      <div className="price-strip">
        <div>
          <div className="ps-label">CMP</div>
          <div className="ps-val">{fmt(pick.price)}</div>
        </div>
        <div>
          <div className="ps-label">RSI</div>
          <div className="ps-val" style={{color: pick.rsi < 40 ? '#00e5a0' : '#f5c842'}}>{pick.rsi}</div>
        </div>
        <div>
          <div className="ps-label">Vol Ratio</div>
          <div className="ps-val">{isPriyank ? pick.vol_ratio : pick.vr}x</div>
        </div>
        <div>
          <div className="ps-label">{isPriyank ? "52W High" : "Darvas Ceiling"}</div>
          <div className="ps-val">{isPriyank ? fmt(pick.w52h) : fmt(pick.box_ceil || pick.w52h)}</div>
        </div>
      </div>

      <div className="chips-row">
        {signals.slice(0, 3).map((s, idx) => {
          const type = isPriyank ? s.type : s.t;
          const label = isPriyank ? s.sig : s.s;
          const cls = type === 'BULL' ? 'green' : type === 'BEAR' ? 'red' : 'yellow';
          return <span key={idx} className={`chip ${cls}`}>{label}</span>;
        })}
      </div>

      <div className="thesis-box">
        <div className="thesis-label">TIMING & SETUP ACTION</div>
        <p className="thesis-text" style={{fontWeight: 700, color: '#fff', marginBottom: '8px'}}>{t.timing}</p>
        <div className="thesis-label">SIGNALS DETECTED</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px'}}>
          {signals.slice(0, 2).map((s, idx) => (
            <div key={idx} style={{fontSize: '0.78rem', color: 'var(--tx)', display: 'flex', gap: '6px', alignItems: 'flex-start'}}>
              <span style={{color: isPriyank ? '#3b82f6' : '#9d7cfc', flexShrink: 0}}>◆</span>
              <span><strong>{isPriyank ? s.sig : s.s}:</strong> {isPriyank ? s.desc : s.d}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="levels-grid">
        <div className="level-item entry">
          <div className="li-label">ENTRY</div>
          <div className="li-val">{fmt(t.entry)}</div>
        </div>
        <div className="level-item sl">
          <div className="li-label">STOP LOSS</div>
          <div className="li-val">{fmt(t.sl)}</div>
          <div className="li-sub">{t.sl_pct}% risk</div>
        </div>
        <div className="level-item t1">
          <div className="li-label">{isPriyank ? "T1 (Fib 61.8)" : "T1 (Range)"}</div>
          <div className="li-val">{fmt(t.t1)}</div>
          <div className="li-sub">RR {t.rr1}:1</div>
        </div>
        <div className="level-item t2">
          <div className="li-label">{isPriyank ? "T2 (Preferred)" : "T2 (Target)"}</div>
          <div className="li-val" style={{color: '#00e5a0'}}>{fmt(t.t2)}</div>
          <div className="li-sub">RR {t.rr2}:1</div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [state, setState] = useState('idle');
  const [data,  setData]  = useState(null);
  const [err,   setErr]   = useState('');
  const [history, setHistory] = useState([]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API}/api/history`);
      if (res.ok) {
        const json = await res.json();
        setHistory(json);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  const clearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear history?")) return;
    try {
      const res = await fetch(`${API}/api/history/clear`, { method: 'POST' });
      if (res.ok) {
        setHistory([]);
      }
    } catch (e) {
      console.error("Failed to clear history", e);
    }
  };

  React.useEffect(() => {
    fetchHistory();
  }, []);

  const runScan = async () => {
    setState('loading');
    setErr('');
    try {
      const res  = await fetch(`${API}/api/scan`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setState('done');
      fetchHistory();
    } catch (e) {
      setErr('Cannot connect to API. Start python api.py');
      setState('error');
    }
  };

  return (
    <div className="app">
      <header className="hdr">
        <div className="hdr-inner">
          <div className="hdr-top">
            <div>
              <div className="hdr-badge" style={{color:'#00e5a0', borderColor:'rgba(0,229,160,.3)'}}>&gt;70% WIN RATE STRATEGY</div>
              <h1>High-Probability Radar</h1>
              <p className="hdr-sub">
                Scanning Nifty 500 for deep oversold pullbacks in massive macro uptrends. Wide stops. High Win Rates.
              </p>
            </div>
            <button className={`scan-btn ${state === 'loading' ? 'scanning' : ''}`} onClick={runScan} disabled={state === 'loading'}>
              {state === 'loading' ? <Spinner /> : <>⚡ Find 70% Setups</>}
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        {state === 'idle' && (
          <div className="empty-state">
            <div className="empty-icon">🎯</div>
            <h2>Ready to find high-probability bounces</h2>
            <p>Click <strong>Find 70% Setups</strong> to scan the Nifty 500 for deep RSI pullbacks in 200-EMA uptrends.</p>
          </div>
        )}
        {state === 'loading' && (
          <div className="loading-state">
            <Spinner />
            <h2>Scanning 500 Stocks for Oversold Pullbacks…</h2>
          </div>
        )}
        {state === 'error' && (
          <div className="error-state">
            <h2>Connection Failed</h2>
            <p>{err}</p>
            <button className="scan-btn" onClick={runScan}>Retry</button>
          </div>
        )}
        {state === 'done' && data && (
          <>
            <NiftyBanner data={data.nifty50} />
            <div className="scan-meta">
              <span>🕐 {data.scan_time}</span>
              <span>📊 Processed: {data.scanned}</span>
              <span>✅ 70%+ Setups Found: {data.found}</span>
            </div>
            {data.picks.length === 0 ? (
              <div className="no-picks">
                <h2>No Extreme Oversold Setups Today</h2>
              </div>
            ) : (
              <div className="cards-grid">
                {data.picks.map((pick, i) => <TradeCard key={pick.sym} pick={pick} rank={i + 1} />)}
              </div>
            )}

            {/* Featured Analyst Setups Section */}
            {(data.priyank_pick || data.darvax_pick) && (
              <div className="analyst-section" style={{marginTop: '3rem'}}>
                <div className="picks-header" style={{marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.8rem'}}>
                  <h2>⚡ Featured Analyst Picks</h2>
                  <p style={{color: 'var(--muted)', fontSize: '0.85rem'}}>Top momentum and breakout plays configured by specialist traders.</p>
                </div>
                <div className="cards-grid">
                  {data.priyank_pick && (
                    <AnalystTradeCard 
                      pick={data.priyank_pick} 
                      analystName="Priyank Sharma" 
                      badgeText="Priyank Sharma Methodology" 
                      colorClass="priyank-card"
                    />
                  )}
                  {data.darvax_pick && (
                    <AnalystTradeCard 
                      pick={data.darvax_pick} 
                      analystName="AmitabhJha3" 
                      badgeText="AmitabhJha3 DarvaX" 
                      colorClass="darvax-card"
                    />
                  )}
                </div>
              </div>
            )}
          </>
        )}

        <HistorySection historyData={history} onClear={clearHistory} />
      </main>
    </div>
  );
}
