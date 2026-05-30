import React from 'react';
import { NIFTY_OPTIONS_DATA } from '../data';
import { AlertTriangle, TrendingUp, TrendingDown, Target, Zap, Shield, CheckCircle2 } from 'lucide-react';

const NiftyOptionsStrategy = () => {
  const data = NIFTY_OPTIONS_DATA;

  return (
    <div className="nifty-options-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
      
      {/* Top Banner - Context */}
      <div className="context-banner" style={{ background: 'var(--panel-bg)', borderRadius: '12px', border: '1px solid var(--border)', padding: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '2rem', alignItems: 'center' }}>
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.2rem' }}>INDEX CONTEXT</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#fff', fontFamily: 'var(--font-heading)' }}>
            NIFTY {data.niftySpot} 
            <span style={{ fontSize: '1rem', color: 'var(--accent-green)', marginLeft: '0.8rem' }}>▲ BULLISH</span>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>INDIA VIX</div>
            <div style={{ color: data.vix < 15 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 'bold', fontSize: '1.1rem' }}>{data.vix}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>PUT-CALL RATIO</div>
            <div style={{ color: data.pcr < 1 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 'bold', fontSize: '1.1rem' }}>{data.pcr}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>NEAREST EXPIRY</div>
            <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.1rem' }}>{data.nearestExpiry}</div>
          </div>
        </div>
      </div>

      {/* Strategies Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {data.strategies.map(strategy => (
          <div key={strategy.id} style={{ background: 'var(--panel-bg)', borderRadius: '12px', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <div style={{ 
              padding: '1rem 1.5rem', 
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              background: strategy.type === 'BUY' ? 'rgba(0, 229, 160, 0.05)' : strategy.type === 'SELL' ? 'rgba(255, 96, 96, 0.05)' : 'rgba(157, 124, 252, 0.05)' 
            }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: strategy.type === 'BUY' ? 'var(--accent-green)' : strategy.type === 'SELL' ? 'var(--accent-red)' : 'var(--accent-purple)' }}>
                {strategy.type === 'BUY' ? <TrendingUp size={18} /> : strategy.type === 'SELL' ? <TrendingDown size={18} /> : <Layers size={18} />}
                {strategy.name}
              </h3>
            </div>
            
            <div style={{ padding: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>TYPE / STRIKE</div>
                  <div style={{ fontWeight: 'bold', color: '#fff', fontSize: '1.1rem' }}>{strategy.optionType} {strategy.strike || strategy.buyStrike}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>PREMIUM</div>
                  <div style={{ fontWeight: 'bold', color: 'var(--accent-purple)', fontSize: '1.1rem' }}>₹{strategy.premium || strategy.netCost}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>STOP LOSS (SL)</div>
                  <div style={{ fontWeight: 'bold', color: 'var(--accent-red)', fontSize: '1.1rem' }}>₹{strategy.slPremium || (strategy.maxLoss / strategy.lotSize).toFixed(0)}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>TARGET (T2)</div>
                  <div style={{ fontWeight: 'bold', color: 'var(--accent-green)', fontSize: '1.1rem' }}>₹{strategy.target2Premium || ((strategy.netCost + (strategy.maxProfit/strategy.lotSize))).toFixed(0)}</div>
                </div>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.3rem' }}>Why Selected?</div>
                <div style={{ fontSize: '0.9rem', color: '#fff', lineHeight: 1.4 }}>{strategy.whySelected}</div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {strategy.signals.map((sig, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                    <CheckCircle2 size={14} color="var(--accent-green)" />
                    <span>{sig}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Rules engine */}
      <div style={{ background: 'var(--panel-bg)', borderRadius: '12px', border: '1px solid var(--border)', padding: '1.5rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff' }}>
          <Shield size={18} color="var(--accent-purple)" />
          Systematic Options Rules
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '0.8rem' }}>
          {data.rules.map((ruleObj, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem', background: 'rgba(0,0,0,0.15)', padding: '0.8rem', borderRadius: '6px' }}>
              <Zap size={14} color="var(--accent-yellow)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: 1.4 }}>
                {ruleObj.rule}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default NiftyOptionsStrategy;
