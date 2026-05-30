import React, { useState } from 'react';
import { PRE_BREAKOUT_DATA } from '../data';
import { Target, Zap, Activity, BarChart2, Maximize2, Shield } from 'lucide-react';

const PreBreakoutRadar = () => {
  const [selectedStock, setSelectedStock] = useState(PRE_BREAKOUT_DATA[0]);

  return (
    <div style={{ display: 'flex', gap: '2rem', height: '100%', marginTop: '1rem' }}>
      
      {/* Left List */}
      <div style={{ flex: '1', minWidth: '350px', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', paddingRight: '10px' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
          <Activity size={18} color="var(--accent-yellow)" />
          Pre-Breakout Accumulation List
        </h3>
        {PRE_BREAKOUT_DATA.map(stock => (
          <div 
            key={stock.id}
            onClick={() => setSelectedStock(stock)}
            style={{ 
              background: selectedStock.id === stock.id ? 'rgba(0, 229, 160, 0.08)' : 'var(--panel-bg)',
              border: `1px solid ${selectedStock.id === stock.id ? 'var(--accent-green)' : 'var(--border)'}`,
              borderRadius: '10px',
              padding: '1.2rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
              <div>
                <div style={{ fontWeight: '900', color: '#fff', fontSize: '1.1rem' }}>{stock.ticker.replace('.NS', '')}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{stock.sector}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: 'var(--accent-yellow)', fontWeight: 'bold', fontSize: '1.2rem' }}>{stock.compressionScore}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>COMPRESSION SCORE</div>
              </div>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <div style={{ color: '#fff' }}>CMP: <span style={{ fontWeight: 'bold' }}>₹{stock.cmp}</span></div>
              <div style={{ color: 'var(--accent-purple)' }}>BRK: ₹{stock.breakoutLevel}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Right Detail Pane */}
      <div style={{ flex: '2', background: 'var(--panel-bg)', borderRadius: '12px', border: '1px solid var(--border)', padding: '2rem', overflowY: 'auto' }}>
        {selectedStock && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
              <div>
                <h2 style={{ margin: '0 0 0.2rem 0', fontSize: '1.8rem', color: '#fff', fontWeight: '900', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                  {selectedStock.name}
                  <span style={{ fontSize: '0.75rem', background: 'rgba(255, 200, 66, 0.15)', color: 'var(--accent-yellow)', padding: '4px 10px', borderRadius: '20px', fontWeight: 'bold', letterSpacing: '1px' }}>
                    PROB: {selectedStock.breakoutProbability}%
                  </span>
                </h2>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{selectedStock.ticker} | {selectedStock.category}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#fff' }}>₹{selectedStock.cmp}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Current Market Price</div>
              </div>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '10px', borderLeft: '3px solid var(--accent-purple)', marginBottom: '2rem' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--accent-purple)', fontWeight: 'bold', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Historical Analogy</div>
              <div style={{ color: '#fff', fontSize: '1.05rem', fontStyle: 'italic' }}>"{selectedStock.exampleAnalogy}"</div>
            </div>

            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Maximize2 size={16} color="var(--accent-green)" />
              Compression & Accumulation Signals
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              {Object.entries(selectedStock.signals).map(([key, signal]) => (
                <div key={key} style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </span>
                    <span style={{ fontSize: '0.7rem', fontWeight: 'bold', color: 'var(--accent-green)', background: 'rgba(0, 229, 160, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      {signal.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff', marginBottom: '0.5rem' }}>{signal.value}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>{signal.note}</div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '2rem' }}>
              <div style={{ flex: 1, background: 'rgba(0, 229, 160, 0.05)', border: '1px solid rgba(0, 229, 160, 0.2)', padding: '1.5rem', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--accent-green)', fontWeight: 'bold' }}>
                  <Zap size={18} />
                  TRADE SETUP
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Breakout Level:</span>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.1rem' }}>₹{selectedStock.breakoutLevel}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Stop Loss:</span>
                  <span style={{ color: 'var(--accent-red)', fontWeight: 'bold', fontSize: '1.1rem' }}>₹{selectedStock.stopLoss}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Risk/Reward:</span>
                  <span style={{ color: 'var(--accent-yellow)', fontWeight: 'bold', fontSize: '1.1rem' }}>1:{selectedStock.rr}</span>
                </div>
              </div>

              <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--accent-purple)', fontWeight: 'bold' }}>
                  <Target size={18} />
                  TARGETS
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Target 1 (Base):</span>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.1rem' }}>₹{selectedStock.targets[0]}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Target 2 (Mid):</span>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.1rem' }}>₹{selectedStock.targets[1]}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Target 3 (Swing):</span>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.1rem' }}>₹{selectedStock.targets[2]}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 style={{ margin: '0 0 0.8rem 0', fontSize: '1rem', color: '#fff' }}>Catalysts</h3>
              <ul style={{ paddingLeft: '1.2rem', margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                {selectedStock.catalysts.map((cat, i) => <li key={i}>{cat}</li>)}
              </ul>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default PreBreakoutRadar;
