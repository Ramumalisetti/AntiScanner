"""
Elite SMC Scanner — API Backend
Scans Nifty 500 / F&O universe for institutional Smart Money Concepts (SMC).

Criteria:
1. Break of Structure (BOS): Recent impulsive bullish wave.
2. Order Block (OB): The last down-candle before the impulsive wave.
3. Fair Value Gap (FVG): Unmitigated bullish imbalance left by the impulsive wave.
4. Liquidity Sweep: Price sweeping below a swing low and rejecting.
5. Mitigation: Current price pulling back into the FVG or OB demand zone.
"""

import time, math, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# UNIVERSE — Loaded dynamically or fallback to small list
# ─────────────────────────────────────────────
UNIVERSE = []
try:
    # Try to load the 504 Nifty 500 stocks if the file exists
    with open('api.py', 'r', encoding='utf-8') as f:
        # Just use a static fallback if we can't parse it easily here, 
        # but I will inject the 504 list explicitly in the script below to be safe.
        pass
except:
    pass

# We will read the universe from universe.json if it exists, else fallback.
import os
if os.path.exists('universe.json'):
    with open('universe.json', 'r') as f:
        UNIVERSE = json.load(f)
else:
    # Fallback minimal universe
    UNIVERSE = [
        {"sym":"HDFCBANK","yf":"HDFCBANK.NS","sector":"Banking"},
        {"sym":"RELIANCE","yf":"RELIANCE.NS","sector":"Energy"},
        {"sym":"TCS","yf":"TCS.NS","sector":"IT"},
        {"sym":"INFY","yf":"INFY.NS","sector":"IT"},
        {"sym":"ICICIBANK","yf":"ICICIBANK.NS","sector":"Banking"}
    ]

# ─────────────────────────────────────────────
# SMC HELPERS
# ─────────────────────────────────────────────
def find_swing_lows(lows, window=5):
    """Find local minima in a series of lows"""
    swings = []
    n = len(lows)
    for i in range(window, n - window):
        is_low = True
        for j in range(i - window, i + window + 1):
            if lows[j] < lows[i]:
                is_low = False
                break
        if is_low:
            swings.append({'idx': i, 'val': lows[i]})
    return swings

def find_order_block(opens, highs, lows, closes):
    """
    Find a bullish order block (last bearish candle before strong bullish momentum)
    Returns: {top, bottom, mid}
    """
    n = len(closes)
    # Look back over last 40 days for the biggest bullish engulfing or momentum
    best_ob = None
    max_momentum = 0
    
    for i in range(n - 40, n - 5):
        # Look for a down candle followed by explosive up moves
        if closes[i] < opens[i]:  # Bearish candle
            # Check momentum of next 2-3 candles
            momentum = closes[i+3] - closes[i]
            if momentum > max_momentum:
                max_momentum = momentum
                best_ob = {
                    'top': highs[i],
                    'bottom': lows[i],
                    'mid': (highs[i] + lows[i]) / 2,
                    'idx': i
                }
    return best_ob

def find_fvg(highs, lows, closes):
    """
    Find the most recent unmitigated bullish Fair Value Gap (FVG).
    FVG occurs when Low of candle 3 > High of candle 1.
    """
    n = len(closes)
    fvgs = []
    # Scan last 30 days
    for i in range(n - 30, n - 2):
        gap_bottom = highs[i]
        gap_top = lows[i+2]
        
        if gap_top > gap_bottom:
            # We have an FVG. Check if it's been mitigated (filled) by any subsequent candle
            mitigated = False
            for j in range(i+3, n):
                if lows[j] <= gap_bottom:
                    mitigated = True
                    break
            
            if not mitigated:
                fvgs.append({
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'idx': i+1
                })
    
    # Return the most recent unmitigated FVG
    return fvgs[-1] if fvgs else None

def check_liquidity_sweep(lows, closes, current_idx, lookback=15):
    """
    Check if the current pullback sweeps a recent swing low but rejects.
    """
    n = len(lows)
    current_low = lows[current_idx]
    current_close = closes[current_idx]
    
    # Find lowest low in lookback window before current candle
    start_idx = max(0, current_idx - lookback)
    recent_lows = lows[start_idx:current_idx]
    if not recent_lows: return False
    
    swing_low = min(recent_lows)
    
    # Sweep condition: price pierced below the swing low, but closed above it
    if current_low < swing_low and current_close > swing_low:
        return True
    return False

# ─────────────────────────────────────────────
# CORE SMC ANALYSIS
# ─────────────────────────────────────────────
def analyze_smc(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 60:
            return None

        closes = df["Close"].values.tolist()
        opens  = df["Open"].values.tolist()
        highs  = df["High"].values.tolist()
        lows   = df["Low"].values.tolist()
        vols   = df["Volume"].values.tolist()
        n = len(closes)

        price = closes[-1]
        
        # Pullback Measure (need some retracement to enter)
        recent_high = max(highs[-20:])
        pullback_pct = round((recent_high - price) / recent_high * 100, 2)
        if pullback_pct < 2.0:
            return None # Not a pullback

        # ── Find SMC Structures ──
        ob = find_order_block(opens, highs, lows, closes)
        fvg = find_fvg(highs, lows, closes)
        liq_sweep = check_liquidity_sweep(lows, closes, -1) or check_liquidity_sweep(lows, closes, -2)
        
        # ── Mitigation Check (Is price in the zone?) ──
        in_ob = False
        in_fvg = False
        support_level = None
        support_name = None
        
        if fvg and (fvg['bottom'] * 0.98 <= price <= fvg['top'] * 1.02):
            in_fvg = True
            support_level = fvg['bottom']
            support_name = "FVG Mitigation"
            
        elif ob and (ob['bottom'] * 0.98 <= price <= ob['top'] * 1.05):
            in_ob = True
            support_level = ob['top']
            support_name = "Demand Order Block"
            
        if not (in_ob or in_fvg or liq_sweep):
            return None # No SMC footprint present

        # ── Volume Profile ──
        avg_vol_20 = float(np.mean(vols[-20:]))
        today_vol = vols[-1]
        vol_ratio = round(today_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
        
        # ── SMC Scoring ──
        score = 0.0
        if in_fvg: score += 3.5
        if in_ob: score += 4.0
        if liq_sweep: score += 3.0
        if vol_ratio > 1.2: score += 1.0
        
        score = min(round(score, 1), 10.0)
        
        if score < 4.0:
            return None

        # ── Risk / Reward ──
        # In SMC, stop loss is strictly below the Order Block or Sweep low
        stop_loss = None
        if liq_sweep:
            stop_loss = min(lows[-2:]) * 0.99
        elif ob:
            stop_loss = ob['bottom'] * 0.99
        elif fvg:
            stop_loss = fvg['bottom'] * 0.99
        else:
            stop_loss = min(lows[-5:]) * 0.99
            
        stop_loss = round(stop_loss, 2)
        risk = price - stop_loss
        if risk <= 0: return None
        
        t1 = round(price + risk * 2.5, 2) # Target old local high / liquidity
        t2 = round(recent_high, 2)        # Target major structural high
        if t2 <= t1: t2 = round(t1 + risk * 1.5, 2)
        
        rr = round((t1 - price) / risk, 1)

        # ── Thesis Generation ──
        thesis_parts = [f"Institutional tracking for {stock['sym']} shows a {pullback_pct:.1f}% corrective pullback."]
        
        if liq_sweep:
            thesis_parts.append("Smart Money has executed a Liquidity Sweep, hunting retail stops below the recent swing low before rejecting upward.")
            
        if in_fvg:
            thesis_parts.append(f"Price is currently mitigating an un-filled Fair Value Gap (FVG) between ₹{fvg['bottom']:.0f} and ₹{fvg['top']:.0f}, balancing the order book.")
            
        if in_ob:
            thesis_parts.append(f"Price has tapped directly into an institutional Demand Order Block (OB) originating at ₹{ob['top']:.0f}, where heavy accumulation previously occurred.")
            
        thesis_parts.append("This presents a high-probability asymmetric entry based on pure institutional market structure.")

        entry_strategy = f"Enter inside the {support_name or 'Liquidity'} zone near ₹{price:.0f}. Invalidation is a hard close below the institutional stop hunt level at ₹{stop_loss:.0f}."

        return {
            "sym":           stock["sym"],
            "sector":        stock["sector"],
            "price":         round(price, 2),
            "score":         score,
            "pullback_pct":  pullback_pct,
            "recent_high":   round(recent_high, 2),
            "support_level": support_level or round(price*0.95, 2),
            "support_name":  support_name or "Liquidity Pool",
            "fvg_active":    in_fvg,
            "ob_active":     in_ob,
            "liq_sweep":     liq_sweep,
            "vol_ratio":     vol_ratio,
            "entry":         round(price, 2),
            "stop_loss":     stop_loss,
            "t1":            t1,
            "t2":            t2,
            "rr":            rr,
            "thesis":        " ".join(thesis_parts),
            "entry_strategy":entry_strategy,
        }
    except Exception as e:
        return None

def fetch_market_structure():
    """Fetch Nifty 50 structure instead of EMAs"""
    try:
        df = yf.Ticker("^NSEI").history(period="3mo", interval="1d", auto_adjust=True)
        c = df["Close"].values.tolist()
        price = c[-1]
        pct_chg = round((c[-1] - c[-2]) / c[-2] * 100, 2) if len(c) > 1 else 0
        
        # Define market structure based on Higher Highs / Lower Lows
        recent_high = max(c[-20:])
        recent_low = min(c[-20:])
        structure = "BULLISH BOS" if price > c[-20] else "BEARISH CHOCH" if price < c[-20] else "CONSOLIDATION"
        
        return {
            "price":  round(price, 2),
            "pct":    pct_chg,
            "structure": structure,
            "premium": price > (recent_high + recent_low)/2
        }
    except:
        return {"price": 0, "pct": 0, "structure": "UNKNOWN", "premium": False}

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────
@app.route('/api/scan', methods=['GET'])
def run_scan():
    t0 = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(analyze_smc, s): s for s in UNIVERSE}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # Sort by score desc, take top 3
    results.sort(key=lambda x: -x["score"])
    top3 = results[:3]

    nifty = fetch_market_structure()
    elapsed = round(time.time() - t0, 1)

    return jsonify({
        "status": "success",
        "scan_time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "elapsed": elapsed,
        "scanned": len(UNIVERSE),
        "found": len(results),
        "nifty50": nifty,
        "picks": top3,
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    print("Elite SMC Scanner API — Starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
