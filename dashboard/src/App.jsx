import React, { useState } from 'react';
import { 
  TrendingUp, 
  Shield, 
  Zap, 
  Volume2, 
  Award, 
  Percent, 
  Calculator, 
  Target, 
  ChevronDown, 
  ChevronUp, 
  Layers, 
  CheckCircle2, 
  AlertTriangle,
  ExternalLink,
  Calendar,
  DollarSign
} from 'lucide-react';
import './App.css';

// Elite stock report dataset based on the Manus AI May 30, 2026 report
const STOCKS_DATA = {
  darvas: [
    {
      id: "cummins",
      name: "Cummins India Ltd",
      ticker: "CUMMINSIND.NS",
      sector: "Capital Goods",
      whySelected: "Cummins India has exhibited a classic Darvas Box breakout on the weekly charts, hitting fresh record highs in May 2026 with massive volume expansion, indicating strong institutional momentum.",
      technical: {
        trend: "Strong Uptrend",
        weekly: "Multi-week consolidation breakout above ₹5,400.",
        daily: "Tight volatility contraction followed by an explosive gap-up and continuation.",
        relativeStrength: "Outperforming Nifty 50 significantly over the last quarter."
      },
      darvas: {
        boxFormation: "Consolidated between ₹5,000 and ₹5,400 for several weeks.",
        breakoutLevel: 5418,
        quality: "Extremely tight, showing accumulation rather than distribution.",
        volume: "Breakout accompanied by 3x the 5-day average volume."
      },
      smc: {
        bos: "Bullish Break of Structure on the daily timeframe.",
        choch: "N/A (Trend continuation).",
        liquiditySweep: "Swept minor lows near ₹5,100 before the breakout.",
        fvg: "Bullish FVG created between ₹5,450 and ₹5,600.",
        demandSupply: "Strong demand zone established at the top of the previous box (₹5,400).",
        footprint: "Heavy delivery-based buying observed post-earnings."
      },
      volume: {
        delivery: "Rising steadily above 55%",
        expansion: "Massive spike on the breakout day.",
        accumulation: "Consistent green volume bars during the box formation."
      },
      strategy: {
        cmp: 6025,
        idealEntry: 6025, // range 6000-6050
        addOn: 5800,
        retest: 5450,
        stopLoss: 5350,
        targets: [6500, 6800, 7200],
        rr: 3.5,
        probScore: 9.0,
        multibaggerScore: 6,
        holdingPeriod: "2-6 weeks"
      }
    },
    {
      id: "jindalsaw",
      name: "Jindal Saw Ltd",
      ticker: "JINDALSAW.NS",
      sector: "Metals - Pipes",
      whySelected: "Jindal Saw is showing a textbook Darvas Box formation near its 52-week highs, with a high-probability breakout setup emerging above the ₹250 level.",
      technical: {
        trend: "Uptrend",
        weekly: "Higher highs and higher lows.",
        daily: "Consolidating in a tight range just below major resistance.",
        relativeStrength: "High relative strength compared to the broader metal sector."
      },
      darvas: {
        boxFormation: "₹220 to ₹252.",
        breakoutLevel: 253,
        quality: "Excellent; price is compressing tightly near the resistance, indicating imminent expansion.",
        volume: "Volume drying up during consolidation, preparing for a volatility expansion."
      },
      smc: {
        bos: "Bullish BOS expected upon clearing ₹253.",
        choch: "Bullish CHOCH occurred at ₹225.",
        liquiditySweep: "Swept sell-side liquidity at ₹218.",
        fvg: "Unmitigated FVG at ₹230.",
        demandSupply: "Demand zone at ₹220-₹225.",
        footprint: "Steady accumulation visible in delivery data."
      },
      volume: {
        delivery: "Consistently above 60%",
        expansion: "Awaiting breakout volume.",
        accumulation: "Price refusing to drop despite broader market weakness."
      },
      strategy: {
        cmp: 248,
        idealEntry: 255,
        addOn: 260,
        retest: 250,
        stopLoss: 235,
        targets: [280, 300, 325],
        rr: 3.0,
        probScore: 8.5,
        multibaggerScore: 7,
        holdingPeriod: "1-4 weeks"
      }
    },
    {
      id: "bse",
      name: "BSE Ltd",
      ticker: "BSE.NS",
      sector: "Capital Markets",
      whySelected: "BSE Ltd has given a clean SMC and Darvas breakout, sweeping liquidity and expanding with massive volume, driven by strong options market activity.",
      technical: {
        trend: "Strong Uptrend",
        weekly: "Multi-month breakout.",
        daily: "Impulsive move followed by a flag consolidation.",
        relativeStrength: "Top 1% of Nifty 500 in relative strength."
      },
      darvas: {
        boxFormation: "₹3,800 to ₹4,150.",
        breakoutLevel: 4150,
        quality: "High; shallow pullbacks.",
        volume: "Breakout volume was 4x the average."
      },
      smc: {
        bos: "Major weekly BOS.",
        choch: "N/A.",
        liquiditySweep: "Swept internal liquidity at ₹3,900 before the explosive move.",
        fvg: "Massive bullish FVG between ₹4,000 and ₹4,100.",
        demandSupply: "Demand block at ₹3,850.",
        footprint: "Clear institutional buying (large block deals observed)."
      },
      volume: {
        delivery: "High delivery volume on up days.",
        expansion: "Significant expansion during the breakout.",
        accumulation: "Institutional accumulation evident before the breakout."
      },
      strategy: {
        cmp: 4200,
        idealEntry: 4225, // range 4200-4250
        addOn: 4300,
        retest: 4150,
        stopLoss: 3950,
        targets: [4600, 4800, 5200],
        rr: 2.8,
        probScore: 8.5,
        multibaggerScore: 8,
        holdingPeriod: "1-3 months"
      }
    }
  ],
  smc: [
    {
      id: "apollo_micro",
      name: "Apollo Micro Systems",
      ticker: "APOLLO.NS",
      sector: "Defence/Aerospace",
      whySelected: "Apollo Micro Systems presents a textbook SMC setup. It has swept retail liquidity, tapped into a deep daily demand order block, and confirmed a Change of Character (CHOCH) to the upside, backed by stellar Q4 FY26 earnings.",
      technical: {
        trend: "Reversal to Uptrend",
        weekly: "Corrective pullback into a major weekly demand zone.",
        daily: "CHOCH confirmed, creating a new bullish structure.",
        relativeStrength: "Improving rapidly post-earnings."
      },
      darvas: {
        boxFormation: "Forming a new base between ₹380 and ₹420.",
        breakoutLevel: 425,
        quality: "Accumulation phase.",
        volume: "Volume drying up on down days, expanding on up days."
      },
      smc: {
        bos: "Bullish BOS confirmed above ₹410.",
        choch: "Bullish CHOCH at ₹395.",
        liquiditySweep: "Swept major sell-side liquidity below ₹380.",
        fvg: "Bullish FVG at ₹400-₹405.",
        demandSupply: "Strong daily Order Block at ₹385.",
        footprint: "Massive volume spike post-earnings indicates smart money entry."
      },
      volume: {
        delivery: "Surged to 65%+ post-earnings.",
        expansion: "5x average volume on the reversal day.",
        accumulation: "Long lower wicks in the demand zone."
      },
      strategy: {
        cmp: 417.85,
        idealEntry: 412.5, // range 410-415
        addOn: 425,
        retest: 400,
        stopLoss: 375,
        targets: [480, 520, 600],
        rr: 3.5,
        probScore: 9.0,
        multibaggerScore: 9,
        holdingPeriod: "1-3 months"
      }
    },
    {
      id: "aubank",
      name: "AU Small Finance Bank",
      ticker: "AUBANK.NS",
      sector: "Banking",
      whySelected: "AU Bank is showing a classic SMC accumulation schematic. It swept liquidity below ₹950, mitigated a major weekly order block, and is now showing strong displacement to the upside.",
      technical: {
        trend: "Reversal to Uptrend",
        weekly: "Bouncing from a major structural support.",
        daily: "Higher highs and higher lows established.",
        relativeStrength: "Outperforming the Bank Nifty index."
      },
      darvas: {
        boxFormation: "₹980 to ₹1,050.",
        breakoutLevel: 1055,
        quality: "Tight compression before expansion.",
        volume: "Steady volume build-up."
      },
      smc: {
        bos: "Bullish BOS at ₹1,020.",
        choch: "Bullish CHOCH at ₹980.",
        liquiditySweep: "Swept equal lows at ₹955.",
        fvg: "Bullish FVG at ₹990-₹1,010.",
        demandSupply: "Weekly demand block at ₹950.",
        footprint: "Institutional buying evident near the ₹950-₹980 zone."
      },
      volume: {
        delivery: "Rising steadily.",
        expansion: "Moderate expansion on up days.",
        accumulation: "Compression in the lower half of the range."
      },
      strategy: {
        cmp: 1048,
        idealEntry: 1015, // range 1010-1020
        addOn: 1055,
        retest: 990,
        stopLoss: 940,
        targets: [1150, 1230, 1350],
        rr: 2.8,
        probScore: 8.0,
        multibaggerScore: 6,
        holdingPeriod: "2-4 months"
      }
    },
    {
      id: "starhealth",
      name: "Star Health & Allied Insurance",
      ticker: "STARHEALTH.NS",
      sector: "Insurance",
      whySelected: "Star Health has formed a massive long-term base and recently showed a strong CHOCH with institutional volume, indicating the end of its markdown phase.",
      technical: {
        trend: "Early Uptrend",
        weekly: "Breaking out of a multi-year descending channel.",
        daily: "Impulsive bullish structure.",
        relativeStrength: "Improving against the broader financial sector."
      },
      darvas: {
        boxFormation: "₹500 to ₹540.",
        breakoutLevel: 545,
        quality: "Long accumulation base.",
        volume: "Volume dry-up followed by recent expansion."
      },
      smc: {
        bos: "Bullish BOS at ₹530.",
        choch: "Major weekly CHOCH at ₹510.",
        liquiditySweep: "Swept all-time lows before reversing.",
        fvg: "Bullish FVG at ₹515.",
        demandSupply: "Massive accumulation block at ₹480-₹500.",
        footprint: "Heavy delivery volumes in the ₹500 zone."
      },
      volume: {
        delivery: "Consistently high (>65%)",
        expansion: "3x average volume on the CHOCH candle.",
        accumulation: "Long base formation (Wyckoff Accumulation)."
      },
      strategy: {
        cmp: 522.85,
        idealEntry: 525, // range 520-530
        addOn: 550,
        retest: 505,
        stopLoss: 475,
        targets: [620, 680, 750],
        rr: 3.2,
        probScore: 8.5,
        multibaggerScore: 8,
        holdingPeriod: "3-6 months"
      }
    }
  ],
  multibagger: [
    {
      id: "vatech",
      name: "VA Tech Wabag Ltd",
      ticker: "WABAG.NS",
      sector: "Infrastructure - Water Management",
      whySelected: "VA Tech Wabag is perfectly positioned to benefit from the Jal Jeevan Mission and global water infrastructure capex. It is breaking out of a massive multi-year consolidation base with strong earnings growth (20% revenue CAGR).",
      technical: {
        trend: "Strong Uptrend",
        weekly: "Multi-year cup and handle breakout.",
        daily: "Consolidating in a high tight flag.",
        relativeStrength: "Sector leader."
      },
      darvas: {
        boxFormation: "Forming a box near all-time highs.",
        breakoutLevel: "Awaiting fresh breakout",
        quality: "Extremely tight, absorbing all selling pressure.",
        volume: "Volume expansion on weekly breakouts."
      },
      smc: {
        bos: "Continuous weekly BOS.",
        choch: "N/A.",
        liquiditySweep: "Swept minor weekly lows before the recent leg up.",
        fvg: "Deep weekly FVGs remain unmitigated, showing extreme momentum.",
        demandSupply: "Strong demand at previous breakout levels.",
        footprint: "FIIs and DIIs consistently increasing stake."
      },
      volume: {
        delivery: "High delivery percentage indicating strong hands holding.",
        expansion: "Massive volume on weekly/monthly charts.",
        accumulation: "Institutional buying visible over the last 4 quarters."
      },
      strategy: {
        cmp: 1250, // Approx base price
        idealEntry: 1250, // Displayed as CMP/accumulation
        addOn: 1350,
        retest: 1100,
        stopLoss: 1062, // 15% standard
        targets: [2500, 3750, 6250],
        rr: 5.0, // 1:5+
        probScore: 9.5,
        multibaggerScore: 10,
        holdingPeriod: "1-3 years"
      }
    },
    {
      id: "sci",
      name: "Shipping Corporation of India (SCI)",
      ticker: "SCI.NS",
      sector: "Logistics/Shipping",
      whySelected: "SCI reported a massive 62.8% YoY increase in standalone net profit. FIIs have increased their stake for 4 consecutive quarters (up to 20.77%). The stock is showing a massive structural breakout.",
      technical: {
        trend: "Strong Uptrend",
        weekly: "Breaking out of a long-term resistance zone.",
        daily: "Impulsive moves with shallow pullbacks.",
        relativeStrength: "Outperforming the logistics sector."
      },
      darvas: {
        boxFormation: "Multi-month box breakout.",
        breakoutLevel: "Cleared major resistance",
        quality: "High quality, volume-backed consolidation.",
        volume: "Explosive volume on earnings breakout."
      },
      smc: {
        bos: "Major weekly BOS.",
        choch: "N/A.",
        liquiditySweep: "Swept liquidity before the earnings announcement.",
        fvg: "Large bullish FVG created post-earnings.",
        demandSupply: "Demand zone established at the pre-earnings consolidation.",
        footprint: "Clear FII accumulation over 4 quarters."
      },
      volume: {
        delivery: "Rising significantly.",
        expansion: "Highest volume in 52 weeks.",
        accumulation: "Smart money accumulated heavily before the Q4 results."
      },
      strategy: {
        cmp: 265, // Approx base price
        idealEntry: 265,
        addOn: 285,
        retest: 245,
        stopLoss: 225, // pre-earnings base
        targets: [397, 530, 795], // +50%, +100%, +200%
        rr: 4.0,
        probScore: 9.0,
        multibaggerScore: 9,
        holdingPeriod: "1-2 years"
      }
    },
    {
      id: "apollo_multi",
      name: "Apollo Micro Systems (Multibagger)",
      ticker: "APOLLO.NS",
      sector: "Defence/Aerospace",
      whySelected: "Fundamental growth (90% YoY profit growth, robust order book) and structural base make it a prime early-stage multibagger candidate in addition to its short-term swing setups.",
      technical: {
        trend: "Strong Uptrend / Reversal",
        weekly: "Breaking out of multi-month base.",
        daily: "Earnings catalyst-driven acceleration.",
        relativeStrength: "Strong relative strength in defense."
      },
      darvas: {
        boxFormation: "Forming base ₹380 - ₹420.",
        breakoutLevel: 425,
        quality: "Excellent accumulation pattern.",
        volume: "Dry-up on retracement, expansion on breakouts."
      },
      smc: {
        bos: "Confirmed above ₹410.",
        choch: "Bullish CHOCH at ₹395.",
        liquiditySweep: "Swept major sell-side liquidity at ₹380.",
        fvg: "Bullish FVG at ₹400-₹405.",
        demandSupply: "Daily order block at ₹385.",
        footprint: "Stellar Q4 earnings catalyst Smart Money entry."
      },
      volume: {
        delivery: "Surged to 65%+",
        expansion: "5x average volume.",
        accumulation: "Long wicks indicating strong absorption of float."
      },
      strategy: {
        cmp: 417.85,
        idealEntry: 417.85,
        addOn: 425,
        retest: 400,
        stopLoss: 375,
        targets: [800, 1200, 2000],
        rr: 5.0, // 1:5+
        probScore: 9.0,
        multibaggerScore: 9,
        holdingPeriod: "2-3 years"
      }
    }
  ]
};

function App() {
  const [activeTab, setActiveTab] = useState('darvas');
  const [capital, setCapital] = useState(100000);
  const [riskPercent, setRiskPercent] = useState(1);
  const [concorExpiryPrice, setConcorExpiryPrice] = useState(463.85);
  
  // Manage accordion state inside stock cards
  const [expandedSections, setExpandedSections] = useState({
    'cummins-tech': true,
    'jindalsaw-tech': false,
    'bse-tech': false,
    'apollo_micro-tech': true,
    'aubank-tech': false,
    'starhealth-tech': false,
    'vatech-tech': true,
    'sci-tech': false,
    'apollo_multi-tech': false
  });

  const toggleSection = (id) => {
    setExpandedSections(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Perform risk calculation logic
  const calculateTradingRisk = (entry, stopLoss, isMultibagger = false) => {
    // Standard numerical entries
    const numEntry = parseFloat(entry);
    const numSL = parseFloat(stopLoss);
    
    if (isNaN(numEntry) || isNaN(numSL) || numEntry <= numSL) {
      return { shares: 0, cost: 0, risk: 0, rr: 0 };
    }

    const totalRiskAmount = capital * (riskPercent / 100);
    const riskPerShare = numEntry - numSL;
    
    let shares = Math.floor(totalRiskAmount / riskPerShare);
    let totalCost = shares * numEntry;

    // Capital constraints
    if (totalCost > capital) {
      shares = Math.floor(capital / numEntry);
      totalCost = shares * numEntry;
    }

    const actualRisk = shares * riskPerShare;

    return {
      shares,
      totalCost,
      actualRisk: actualRisk > 0 ? actualRisk : 0
    };
  };

  // CONCOR Bear Put Spread payoff calculations
  const calculateConcorPayoff = () => {
    const lotSize = 1000;
    const longPutStrike = 470;
    const longPutPremium = 15.75;
    const shortPutStrike = 450;
    const shortPutPremium = 7.45;
    const netDebit = longPutPremium - shortPutPremium; // 8.30

    // At expiry value
    const longPutValue = Math.max(0, longPutStrike - concorExpiryPrice);
    const shortPutValue = Math.max(0, shortPutStrike - concorExpiryPrice);
    const netValue = longPutValue - shortPutValue;
    const netProfitPerShare = netValue - netDebit;
    const totalProfit = netProfitPerShare * lotSize;

    return {
      netDebit: netDebit * lotSize,
      maxLoss: netDebit * lotSize,
      maxProfit: (20 - netDebit) * lotSize,
      currentPayoff: totalProfit,
      isProfit: totalProfit >= 0
    };
  };

  const concorPayoff = calculateConcorPayoff();

  // Helper to format currency
  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="app-container">
      {/* Premium Dashboard Header */}
      <header className="header">
        <div className="header-left">
          <div className="badge-row">
            <span className="badge-manus">Elite Institutional Analytics</span>
            <span className="badge-universe">NIFTY 500 UNIVERSE</span>
            <span className="badge-universe">CASH & F&O</span>
          </div>
          <h1 className="header-title">Indian Stock Market Report</h1>
          <p className="header-subtitle">High-conviction Swing Setups (Darvas Box & Smart Money Concepts) & Early-Stage Multibaggers</p>
        </div>
        <div className="header-right">
          <div className="date-badge">
            <Calendar size={14} style={{ marginRight: '6px', verticalAlign: 'middle', display: 'inline' }} />
            May 30, 2026
          </div>
          <div className="author-info">Author: Manus AI (Proprietary Swing Trader)</div>
        </div>
      </header>

      {/* Quick Status Stats Row */}
      <section className="stats-bar">
        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: 'var(--accent-purple-glow)' }}>
            <Award size={20} color="var(--accent-purple)" />
          </div>
          <div className="stat-info">
            <span className="stat-label">Safest Setup</span>
            <span className="stat-value">Cummins India</span>
            <span className="stat-subtext">Darvas Consolidation Breakout</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: 'var(--accent-red-glow)' }}>
            <Zap size={20} color="var(--accent-red)" />
          </div>
          <div className="stat-info">
            <span className="stat-label">Aggressive High Beta</span>
            <span className="stat-value">Apollo Micro Systems</span>
            <span className="stat-subtext">Defence Catalyst + 1:3.5+ RR</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: 'var(--accent-blue-glow)' }}>
            <Volume2 size={20} color="var(--accent-blue)" />
          </div>
          <div className="stat-info">
            <span className="stat-label">Highest Vol Spike</span>
            <span className="stat-value">BSE Ltd</span>
            <span className="stat-subtext">4x Average Daily Volume</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: 'var(--accent-green-glow)' }}>
            <TrendingUp size={20} color="var(--accent-green)" />
          </div>
          <div className="stat-info">
            <span className="stat-label">Bearish Hedged Spread</span>
            <span className="stat-value">CONCOR Bear Put</span>
            <span className="stat-subtext">Defined Risk Ratio 1:1.4</span>
          </div>
        </div>
      </section>

      {/* Global Risk Calculator Banner */}
      <section className="stat-card" style={{ background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.08), rgba(59, 130, 246, 0.08))', border: '1px solid rgba(168, 85, 247, 0.25)', flexWrap: 'wrap', justifyContent: 'space-between', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div className="stat-icon-wrapper" style={{ background: 'var(--accent-purple)' }}>
            <Calculator size={22} color="#fff" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontFamily: 'var(--font-heading)' }}>Interactive Capital Allocation Calculator</h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>Set your variables below. Position sizes for all stocks are calculated automatically inside their cards.</p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
          <div className="input-grp" style={{ minWidth: '150px' }}>
            <label style={{ fontSize: '0.65rem', fontWeight: '800', color: 'var(--accent-purple)' }}>Trading Capital</label>
            <input 
              type="number" 
              value={capital} 
              onChange={(e) => setCapital(Math.max(1000, parseFloat(e.target.value) || 0))}
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', padding: '0.4rem 0.6rem', fontWeight: 'bold' }}
            />
          </div>
          <div className="input-grp" style={{ minWidth: '100px' }}>
            <label style={{ fontSize: '0.65rem', fontWeight: '800', color: 'var(--accent-purple)' }}>Max Risk per Trade %</label>
            <input 
              type="number" 
              step="0.25"
              value={riskPercent} 
              onChange={(e) => setRiskPercent(Math.max(0.1, parseFloat(e.target.value) || 0))}
              style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', padding: '0.4rem 0.6rem', fontWeight: 'bold' }}
            />
          </div>
        </div>
      </section>

      {/* Tabs Navigation */}
      <nav className="tabs-container">
        <button 
          className={`tab-btn ${activeTab === 'darvas' ? 'active' : ''}`}
          onClick={() => setActiveTab('darvas')}
        >
          <Shield size={16} />
          Darvas Box Swing Picks
        </button>
        <button 
          className={`tab-btn ${activeTab === 'smc' ? 'active' : ''}`}
          onClick={() => setActiveTab('smc')}
        >
          <Layers size={16} />
          SMC / Hold With Priyank
        </button>
        <button 
          className={`tab-btn ${activeTab === 'multibagger' ? 'active' : ''}`}
          onClick={() => setActiveTab('multibagger')}
        >
          <TrendingUp size={16} />
          Early-Stage Multibaggers
        </button>
        <button 
          className={`tab-btn ${activeTab === 'options' ? 'active' : ''}`}
          onClick={() => setActiveTab('options')}
        >
          <Zap size={16} />
          CONCOR Options Strategy
        </button>
        <button 
          className={`tab-btn ${activeTab === 'rankings' ? 'active' : ''}`}
          onClick={() => setActiveTab('rankings')}
        >
          <Award size={16} />
          Rankings & Summary
        </button>
      </nav>

      {/* Content Panels */}
      {activeTab === 'darvas' && (
        <div className="tab-panel">
          <div className="section-desc">
            <strong>Darvas Box Theory (Amitabh Jha style)</strong> focuses on identifying stocks in strong uptrends consolidating inside tight price corridors. A clean breakout out of the top of the box on above-average institutional volume signals buy entry.
          </div>
          <div className="stocks-grid">
            {STOCKS_DATA.darvas.map(stock => (
              <StockCard 
                key={stock.id}
                stock={stock}
                capital={capital}
                riskPercent={riskPercent}
                calcRisk={calculateTradingRisk}
                formatCurrency={formatCurrency}
                expanded={expandedSections[`${stock.id}-tech`]}
                toggleExpand={() => toggleSection(`${stock.id}-tech`)}
                isMultibagger={false}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'smc' && (
        <div className="tab-panel">
          <div className="section-desc">
            <strong>Smart Money Concepts (Hold With Priyank style)</strong> seeks to identify where banks and institutions are actively positioning. Key triggers include Liquidity Sweeps (flushing out retail stops), Change of Character (CHOCH - early trend shifts), and mitigation of unmitigated Order Blocks/Fair Value Gaps (FVG).
          </div>
          <div className="stocks-grid">
            {STOCKS_DATA.smc.map(stock => (
              <StockCard 
                key={stock.id}
                stock={stock}
                capital={capital}
                riskPercent={riskPercent}
                calcRisk={calculateTradingRisk}
                formatCurrency={formatCurrency}
                expanded={expandedSections[`${stock.id}-tech`]}
                toggleExpand={() => toggleSection(`${stock.id}-tech`)}
                isMultibagger={false}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'multibagger' && (
        <div className="tab-panel">
          <div className="section-desc">
            <strong>Early-Stage Multibagger Picks</strong> represent structurally transformed businesses riding powerful macro tailwinds (Jal Jeevan Mission water infrastructure capex, defense modernization, global logistics expansions) backed by triple-digit profit growths and consistent FII/DII accumulation.
          </div>
          <div className="stocks-grid">
            {STOCKS_DATA.multibagger.map(stock => (
              <StockCard 
                key={stock.id}
                stock={stock}
                capital={capital}
                riskPercent={riskPercent}
                calcRisk={calculateTradingRisk}
                formatCurrency={formatCurrency}
                expanded={expandedSections[`${stock.id}-tech`]}
                toggleExpand={() => toggleSection(`${stock.id}-tech`)}
                isMultibagger={true}
              />
            ))}
          </div>
        </div>
      )}

      {activeTab === 'options' && (
        <div className="tab-panel">
          <div className="section-desc">
            <strong>Bear Put Spread (Hedged Options Strategy)</strong>: CONCOR is exhibiting structural distribution. Buying an In-The-Money put and selling an Out-Of-The-Money put creates a hedged, high-probability defined-risk bearish position.
          </div>

          <div className="options-container">
            {/* Options visualizer slider pane */}
            <div className="options-visualizer-pane">
              <div className="strategy-headline">
                <div className="strategy-title">
                  <h3>Bear Put Spread</h3>
                  <span className="strategy-spot">Container Corporation of India (CONCOR) • Spot: ₹463.85</span>
                </div>
                <div className="strategy-metric-badges">
                  <span className="stock-tag tag-bearish">Bearish Structure</span>
                </div>
              </div>

              {/* Strategy Legs */}
              <div className="options-legs-grid">
                <div className="option-leg-card" style={{ borderLeft: '3px solid var(--accent-blue)' }}>
                  <div className="leg-header">
                    <span className="leg-tag leg-tag-buy">BUY LEG (LONG)</span>
                    <span className="premium-pill">-₹15.75</span>
                  </div>
                  <span className="leg-strike">₹470 Put Option</span>
                  <span className="leg-details">1 Lot (1,000 qty) • Expiry: 30-Jun-2026</span>
                </div>

                <div className="option-leg-card" style={{ borderLeft: '3px solid var(--accent-gold)' }}>
                  <div className="leg-header">
                    <span className="leg-tag leg-tag-sell">SELL LEG (SHORT)</span>
                    <span className="premium-pill">+₹7.45</span>
                  </div>
                  <span className="leg-strike">₹450 Put Option</span>
                  <span className="leg-details">1 Lot (1,000 qty) • Expiry: 30-Jun-2026</span>
                </div>
              </div>

              {/* Simulator Slider */}
              <div className="interactive-simulator">
                <div className="sim-header">
                  <span className="sim-title">Payoff Simulation at Expiry</span>
                  <div className="expiry-price-display">
                    Expiry Price: ₹{concorExpiryPrice.toFixed(2)}
                  </div>
                </div>
                
                <div className="slider-container">
                  <input 
                    type="range" 
                    min="420" 
                    max="500" 
                    step="1"
                    className="expiry-slider" 
                    value={concorExpiryPrice}
                    onChange={(e) => setConcorExpiryPrice(parseFloat(e.target.value))}
                  />
                  <div className="slider-ticks">
                    <span>₹420 (Strong Bearish)</span>
                    <span>₹450 (Max Profit)</span>
                    <span>₹470 (Breakeven)</span>
                    <span>₹500 (Bullish Reversal)</span>
                  </div>
                </div>
              </div>

              {/* Dynamic Payoff Metrics */}
              <div className="payoff-metrics">
                <div className="payoff-card">
                  <span className="payoff-lbl">Net Cost (Max Loss)</span>
                  <span className="payoff-val" style={{ color: '#fff' }}>
                    {formatCurrency(8300)}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-dark)' }}>Premium Debit (₹8.30 * 1,000)</span>
                </div>
                <div className="payoff-card">
                  <span className="payoff-lbl">Simulation Payoff</span>
                  <span className={`payoff-val ${concorPayoff.currentPayoff >= 0 ? 'payoff-val-profit' : 'payoff-val-loss'}`}>
                    {concorPayoff.currentPayoff >= 0 ? '+' : ''}{formatCurrency(concorPayoff.currentPayoff)}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-dark)' }}>At ₹{concorExpiryPrice.toFixed(2)} Expiry</span>
                </div>
              </div>

              {/* Visual gauge bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                  <span>Max Loss (-{formatCurrency(8300)})</span>
                  <span>Breakeven (₹461.70)</span>
                  <span>Max Profit (+{formatCurrency(11700)})</span>
                </div>
                <div className="payoff-bar-bg">
                  <div 
                    className="payoff-bar-fill" 
                    style={{ 
                      width: `${((concorPayoff.currentPayoff + 8300) / 20000) * 100}%`,
                      background: concorPayoff.currentPayoff >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
                    }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Bearish Option Thesis Text */}
            <div className="option-strategy-info" style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '24px', padding: '2rem', backdropFilter: 'blur(16px)' }}>
              <h3 style={{ margin: 0, fontFamily: 'var(--font-heading)', fontSize: '1.4rem' }}>Bearish Core Thesis</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--accent-red)', fontSize: '0.9rem', display: 'block', marginBottom: '0.25rem' }}>Wyckoff Distribution & BOS</strong>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>CONCOR is exhibiting a classic distribution phase. The stock swept buy-side liquidity at the highs (bull trap above ₹480) and immediately reversed, confirming a daily bearish Break of Structure (BOS) below ₹470.</p>
                </div>

                <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--accent-red)', fontSize: '0.9rem', display: 'block', marginBottom: '0.25rem' }}>Bearish Fair Value Gap (FVG)</strong>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>An unmitigated bearish Fair Value Gap exists between ₹475 and ₹485, creating a heavy supply block. The logistics sector is showing relative weakness.</p>
                </div>

                <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--accent-red)', fontSize: '0.9rem', display: 'block', marginBottom: '0.25rem' }}>Options Chain Buildup</strong>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>Substantial Open Interest (OI) buildup observed in Out-of-the-Money calls at ₹480 and ₹500 strikes, representing solid institutional resistance, accompanied by put unwinding.</p>
                </div>
              </div>

              <div style={{ background: 'rgba(255, 74, 90, 0.05)', border: '1px solid rgba(255, 74, 90, 0.15)', borderRadius: '16px', padding: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertTriangle size={16} color="var(--accent-red)" />
                  Spread Parameters & Risk
                </h4>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <li><strong>Ideal Entry Spot:</strong> ₹465 - ₹475 (on pullback to FVG)</li>
                  <li><strong>Net Cost:</strong> ₹8.30 (Premium Debit of ₹8,300 per lot)</li>
                  <li><strong>Max Profit:</strong> ₹11.70 (₹11,700 per lot if spot &lt; ₹450)</li>
                  <li><strong>Risk-Reward Ratio:</strong> 1:1.41</li>
                  <li><strong>Hard Stop Loss:</strong> Exit spread if daily close &gt; ₹485 (invalidates FVG and bearish structure)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'rankings' && (
        <div className="tab-panel">
          <div className="section-desc">
            <strong>Proprietary Category Rankings & Identifications</strong> summarizes the highest conviction structures in the market as of May 30, 2026.
          </div>

          <div className="winners-grid">
            <div className="winner-card winner-card-darvas">
              <h3 className="winner-section-title">
                <Shield size={18} color="var(--accent-blue)" />
                Top Darvas Swing Winners
              </h3>
              <div className="winner-list">
                <div className="winner-item">
                  <div className="winner-rank">1</div>
                  <div className="winner-info">
                    <span className="winner-name">Cummins India Ltd</span>
                    <span className="winner-sub">Weekly box breakout (9/10 score)</span>
                  </div>
                </div>
                <div className="winner-item">
                  <div className="winner-rank">2</div>
                  <div className="winner-info">
                    <span className="winner-name">BSE Ltd</span>
                    <span className="winner-sub">4x breakout volume (8.5/10 score)</span>
                  </div>
                </div>
                <div className="winner-item">
                  <div className="winner-rank">3</div>
                  <div className="winner-info">
                    <span className="winner-name">Jindal Saw Ltd</span>
                    <span className="winner-sub">Volatility contraction base (8.5/10)</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="winner-card winner-card-smc">
              <h3 className="winner-section-title">
                <Layers size={18} color="var(--accent-purple)" />
                Top SMC Swing Winners
              </h3>
              <div className="winner-list">
                <div className="winner-item">
                  <div className="winner-rank">1</div>
                  <div className="winner-info">
                    <span className="winner-name">Apollo Micro Systems</span>
                    <span className="winner-sub">Liquidity sweep + CHOCH (9/10 score)</span>
                  </div>
                </div>
                <div className="winner-item">
                  <div className="winner-rank">2</div>
                  <div className="winner-info">
                    <span className="winner-name">Star Health & Allied Ins.</span>
                    <span className="winner-sub">Early Wyckoff base breakout (8.5/10)</span>
                  </div>
                </div>
                <div className="winner-item">
                  <div className="winner-rank">3</div>
                  <div className="winner-info">
                    <span className="winner-name">AU Small Finance Bank</span>
                    <span className="winner-sub">Weekly order block bounce (8/10)</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="winner-card winner-card-multi">
              <h3 className="winner-section-title">
                <TrendingUp size={18} color="var(--accent-gold)" />
                Top Multibaggers (Long-Term)
              </h3>
              <div className="winner-list">
                <div className="winner-item">
                  <div className="winner-rank">1</div>
                  <div className="winner-info">
                    <span className="winner-name">VA Tech Wabag Ltd</span>
                    <span className="winner-sub">Water macro tailwind (10/10 potential)</span>
                  </div>
                </div>
                <div className="winner-item">
                  <div className="winner-rank">2</div>
                  <div className="winner-info">
                    <span className="winner-name">Shipping Corp of India (SCI)</span>
                    <span className="winner-sub">4 quarters of FII buying (9/10 potential)</span>
                  </div>
                </div>
                <div className="winner-item">
                  <div className="winner-rank">3</div>
                  <div className="winner-info">
                    <span className="winner-name">Apollo Micro Systems</span>
                    <span className="winner-sub">90% profit growth defense (9/10)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <h3 style={{ margin: '1.5rem 0 0.5rem 0', fontFamily: 'var(--font-heading)', fontSize: '1.3rem' }}>Key Identifications</h3>
          <div className="category-highlights">
            <div className="highlight-item-card">
              <span className="hl-category" style={{ color: 'var(--accent-blue)' }}>Safest Setup</span>
              <span className="hl-stock">Cummins India Ltd</span>
              <span className="hl-detail">Strong large-cap backing, robust earnings delivery, cleanest Darvas box breakout with strong historical support.</span>
            </div>

            <div className="highlight-item-card">
              <span className="hl-category" style={{ color: 'var(--accent-red)' }}>Aggressive Growth Catalyst</span>
              <span className="hl-stock">Apollo Micro Systems</span>
              <span className="hl-detail">High beta structure with strong earnings catalyst, Defense capex theme, tight stop loss allowing a 1:3.5+ RR.</span>
            </div>

            <div className="highlight-item-card">
              <span className="hl-category" style={{ color: 'var(--accent-gold)' }}>Long-Term Accumulation</span>
              <span className="hl-stock">SCI Ltd & Star Health</span>
              <span className="hl-detail">SCI exhibits 4 straight quarters of FII accumulation. Star Health represents the earliest phase of channel breakout.</span>
            </div>
          </div>
        </div>
      )}

      {/* Footer copyright */}
      <footer className="footer">
        <div className="footer-left">
          <CheckCircle2 size={14} color="var(--accent-green)" />
          <span>Manus AI Elite proprietary analysis • Confidential</span>
        </div>
        <div className="footer-right">
          <span>Target levels are projections based on structures as of May 30, 2026. Exercise sound risk management.</span>
        </div>
      </footer>
    </div>
  );
}

// Sub-component for individual stock layouts
function StockCard({ stock, capital, riskPercent, calcRisk, formatCurrency, expanded, toggleExpand, isMultibagger }) {
  const riskAnalysis = calcRisk(stock.strategy.idealEntry, stock.strategy.stopLoss);
  
  return (
    <article className="stock-card">
      {/* Card header */}
      <div className="stock-card-header">
        <div className="stock-info-main">
          <div className="stock-avatar">
            {stock.name.charAt(0)}
          </div>
          <div className="stock-title-wrap">
            <h3 className="stock-name">{stock.name}</h3>
            <div className="stock-meta-row">
              <span className="stock-sector">{stock.sector}</span>
              <span className="separator-dot"></span>
              <span className="stock-sector" style={{ fontFamily: 'monospace' }}>{stock.ticker}</span>
              <span className="separator-dot"></span>
              <span className="stock-tag tag-bullish">Bullish Structure</span>
            </div>
          </div>
        </div>

        <div className="stock-scores">
          <div className="score-badge">
            <span className="score-lbl">Conviction</span>
            <span className="score-val score-val-green">{stock.strategy.probScore}/10</span>
          </div>
          <div className="score-badge">
            <span className="score-lbl">{isMultibagger ? "Potential" : "Multibagger"}</span>
            <span className="score-val score-val-gold">{stock.strategy.multibaggerScore}/10</span>
          </div>
        </div>
      </div>

      {/* Body panel */}
      <div className="stock-card-body">
        
        {/* Left Side: Text and Accordion Technicals */}
        <div className="stock-details-pane">
          
          {/* Why Selected Block */}
          <div className="stock-why-box">
            <div className="why-title">
              <CheckCircle2 size={16} />
              Investment Rationale
            </div>
            <p className="why-text">{stock.whySelected}</p>
          </div>

          {/* Core trading metrics specs */}
          <div className="specs-grid">
            <div className="spec-item">
              <span className="spec-lbl">Primary Trend</span>
              <span className="spec-val">{stock.technical.trend}</span>
            </div>
            <div className="spec-item">
              <span className="spec-lbl">CMP (Reference)</span>
              <span className="spec-val" style={{ fontFamily: 'var(--font-heading)', fontWeight: 'bold' }}>
                ₹{stock.strategy.cmp.toFixed(2)}
              </span>
            </div>
            <div className="spec-item">
              <span className="spec-lbl">Holding Period</span>
              <span className="spec-val">{stock.strategy.holdingPeriod}</span>
            </div>
            <div className="spec-item">
              <span className="spec-lbl">Risk:Reward Ratio</span>
              <span className="spec-val" style={{ color: 'var(--accent-green)', fontWeight: 'bold' }}>
                1:{stock.strategy.rr}
              </span>
            </div>
          </div>

          {/* Technical and structure detail accordions */}
          <div className="analysis-accordions">
            <div className="accordion-tab">
              <button className="accordion-header" onClick={toggleExpand}>
                <span className="accordion-title">
                  <Layers size={14} color="var(--accent-purple)" />
                  Technical Analysis & Structure Details
                </span>
                {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              
              {expanded && (
                <div className="accordion-content">
                  <div className="analysis-row">
                    <span className="analysis-key">Weekly Structure:</span>
                    <span className="analysis-val">{stock.technical.weekly}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Daily Structure:</span>
                    <span className="analysis-val">{stock.technical.daily}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Relative Strength:</span>
                    <span className="analysis-val">{stock.technical.relativeStrength}</span>
                  </div>

                  <hr style={{ borderColor: 'rgba(255,255,255,0.03)', margin: '0.75rem 0' }} />
                  
                  <div style={{ fontWeight: 'bold', color: '#fff', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
                    SMART MONEY CONCEPTS FOOTPRINT
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">BOS:</span>
                    <span className="analysis-val">{stock.smc.bos}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">CHOCH:</span>
                    <span className="analysis-val">{stock.smc.choch}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Liquidity Sweep:</span>
                    <span className="analysis-val">{stock.smc.liquiditySweep}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Unmitigated FVG:</span>
                    <span className="analysis-val">{stock.smc.fvg}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Demand / Order Block:</span>
                    <span className="analysis-val">{stock.smc.demandSupply}</span>
                  </div>
                  
                  <hr style={{ borderColor: 'rgba(255,255,255,0.03)', margin: '0.75rem 0' }} />
                  
                  <div style={{ fontWeight: 'bold', color: '#fff', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
                    DARVAS & VOLUME DYNAMICS
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Box Details:</span>
                    <span className="analysis-val">{stock.darvas.boxFormation} (Breakout: ₹{stock.darvas.breakoutLevel})</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Delivery %:</span>
                    <span className="analysis-val">{stock.volume.delivery}</span>
                  </div>
                  <div className="analysis-row">
                    <span className="analysis-key">Volume expansion:</span>
                    <span className="analysis-val">{stock.volume.expansion}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Right Side: Strategy Levels and Position Sizing Calculator */}
        <div className="stock-calc-pane">
          <h4 className="pane-title">
            <Target size={16} color="var(--accent-purple)" />
            Tactical Trade Parameters
          </h4>

          <div className="trading-levels">
            <div className="level-row">
              <span className="level-lbl">IDEAL ENTRY ZONE</span>
              <span className="level-val level-val-green">
                ₹{typeof stock.strategy.idealEntry === 'number' ? stock.strategy.idealEntry.toFixed(2) : stock.strategy.idealEntry}
              </span>
            </div>
            
            <div className="level-row">
              <span className="level-lbl">STOP LOSS (HARD)</span>
              <span className="level-val level-val-red">
                ₹{typeof stock.strategy.stopLoss === 'number' ? stock.strategy.stopLoss.toFixed(2) : stock.strategy.stopLoss}
              </span>
            </div>

            <div className="level-row">
              <span className="level-lbl">TARGET 1</span>
              <span className="level-val level-val-green">
                ₹{typeof stock.strategy.targets[0] === 'number' ? stock.strategy.targets[0].toFixed(2) : stock.strategy.targets[0]}
              </span>
            </div>
            <div className="level-row">
              <span className="level-lbl">TARGET 2</span>
              <span className="level-val" style={{ color: '#fff' }}>
                ₹{typeof stock.strategy.targets[1] === 'number' ? stock.strategy.targets[1].toFixed(2) : stock.strategy.targets[1]}
              </span>
            </div>
            <div className="level-row">
              <span className="level-lbl">TARGET 3</span>
              <span className="level-val" style={{ color: '#fff' }}>
                ₹{typeof stock.strategy.targets[2] === 'number' ? stock.strategy.targets[2].toFixed(2) : stock.strategy.targets[2]}
              </span>
            </div>
          </div>

          {/* Dynamic position sizing calculations */}
          {typeof stock.strategy.idealEntry === 'number' && typeof stock.strategy.stopLoss === 'number' && (
            <div className="calculator-box">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 'bold' }}>
                <Calculator size={14} color="var(--accent-purple)" />
                Position Planner (Active Target)
              </div>
              
              <div className="calc-results">
                <div className="result-row">
                  <span className="result-lbl">Recommended Shares:</span>
                  <span className="result-val result-val-highlight">{riskAnalysis.shares} qty</span>
                </div>
                <div className="result-row">
                  <span className="result-lbl">Capital Required:</span>
                  <span className="result-val">{formatCurrency(riskAnalysis.totalCost)}</span>
                </div>
                <div className="result-row">
                  <span className="result-lbl">Total Stoploss Risk:</span>
                  <span className="result-val" style={{ color: 'var(--accent-red)' }}>{formatCurrency(riskAnalysis.actualRisk)}</span>
                </div>
                
                {riskAnalysis.shares > 0 && (
                  <div className="target-projected">
                    <span className="target-projected-title">Projected Net Profits</span>
                    <div className="result-row">
                      <span className="result-lbl">T1 Return:</span>
                      <span className="result-val" style={{ color: 'var(--accent-green)' }}>
                        +{formatCurrency(riskAnalysis.shares * (stock.strategy.targets[0] - stock.strategy.idealEntry))}
                      </span>
                    </div>
                    <div className="result-row">
                      <span className="result-lbl">T2 Return:</span>
                      <span className="result-val" style={{ color: 'var(--accent-green)' }}>
                        +{formatCurrency(riskAnalysis.shares * (stock.strategy.targets[1] - stock.strategy.idealEntry))}
                      </span>
                    </div>
                    <div className="result-row">
                      <span className="result-lbl">T3 Return:</span>
                      <span className="result-val" style={{ color: 'var(--accent-green)' }}>
                        +{formatCurrency(riskAnalysis.shares * (stock.strategy.targets[2] - stock.strategy.idealEntry))}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

      </div>

      {/* Footer indicator details */}
      <div className="stock-card-footer">
        <span>Structure sweeps verified under daily filters.</span>
        <span>Risk Warning: Hard stop loss triggers on daily close below level.</span>
      </div>
    </article>
  );
}

export default App;
