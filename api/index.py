"""
High-Probability Confluence Scanner — API Backend
Targeting >70% Win Rate.
Blends SMC Demand Zones with Classic Mean Reversion (RSI, EMA, ATR).
"""

import time, math, json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# UNIVERSE
# ─────────────────────────────────────────────
UNIVERSE = []
if os.path.exists('universe.json'):
    with open('universe.json', 'r') as f:
        UNIVERSE = json.load(f)
else:
    UNIVERSE = [{"sym":"HDFCBANK","yf":"HDFCBANK.NS","sector":"Banking"}]

# ─────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────
def calc_rsi(closes, window=14):
    if len(closes) < window + 1: return 50
    diffs = np.diff(closes)
    gains = np.where(diffs > 0, diffs, 0)
    losses = np.where(diffs < 0, -diffs, 0)
    avg_gain = np.mean(gains[-window:])
    avg_loss = np.mean(losses[-window:])
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_atr(highs, lows, closes, window=14):
    if len(closes) < window + 1: return 0
    tr = []
    for i in range(1, len(closes)):
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))
    return np.mean(tr[-window:])

def find_order_block(opens, highs, lows, closes):
    n = len(closes)
    best_ob = None
    max_momentum = 0
    for i in range(n - 40, n - 5):
        if closes[i] < opens[i]:  
            momentum = closes[i+3] - closes[i]
            if momentum > max_momentum:
                max_momentum = momentum
                best_ob = {'top': highs[i], 'bottom': lows[i]}
    return best_ob

# ─────────────────────────────────────────────
# CORE ANALYSIS
# ─────────────────────────────────────────────
def analyze_confluence(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 200:
            return None

        closes = df["Close"].values
        opens  = df["Open"].values
        highs  = df["High"].values
        lows   = df["Low"].values
        vols   = df["Volume"].values

        price = closes[-1]
        
        # ── 1. Macro Trend (EMAs) ──
        ema50 = np.mean(closes[-50:])
        ema200 = np.mean(closes[-200:])
        
        # Must be in a clear uptrend for high win rate
        if price < ema200 or ema50 < ema200:
            return None
            
        # ── 2. Pullback & RSI ──
        recent_high = max(highs[-30:])
        pullback_pct = round((recent_high - price) / recent_high * 100, 2)
        if pullback_pct < 3.0:
            return None # Need a meaningful dip
            
        rsi = calc_rsi(closes)
        # We want oversold conditions for a high probability bounce
        if rsi > 45: 
            return None
            
        # ── 3. SMC / Demand Zone Confluence ──
        ob = find_order_block(opens, highs, lows, closes)
        ob_active = False
        if ob and (ob['bottom'] * 0.95 <= price <= ob['top'] * 1.05):
            ob_active = True
            
        # ── 4. ATR Wide Stop Loss (2x ATR) ──
        atr = calc_atr(highs, lows, closes)
        stop_loss = price - (atr * 2.0)
        risk = price - stop_loss
        
        if risk <= 0: return None
        
        # ── 5. Conservative Target (exactly 5% bounce) ──
        target = price * 1.05
        
        # Must not be targeting higher than the recent macro high (unrealistic)
        if target > recent_high * 1.05:
            return None
            
        # ── Scoring ──
        score = 5.0
        if rsi < 35: score += 2.0
        if ob_active: score += 2.0
        if pullback_pct > 5.0: score += 1.0
        
        if score < 6.0: return None
        
        # ── Thesis ──
        thesis = f"High-probability confluence setup. {stock['sym']} is in a macro uptrend (>200 EMA) but deeply oversold short-term (RSI {rsi:.1f}). "
        if ob_active:
            thesis += f"Price has pulled back {pullback_pct}% directly into a historical Demand Order Block. "
        thesis += f"A wide 2x ATR stop loss (₹{stop_loss:.2f}) protects against market noise, targeting a flat 5.0% profit target (₹{target:.2f})."

        rr = round((target - price) / risk, 2)

        return {
            "sym":           stock["sym"],
            "sector":        stock["sector"],
            "price":         round(price, 2),
            "score":         round(score, 1),
            "pullback_pct":  pullback_pct,
            "rsi":           round(rsi, 1),
            "ema50":         round(ema50, 2),
            "ema200":        round(ema200, 2),
            "atr":           round(atr, 2),
            "ob_active":     ob_active,
            "entry":         round(price, 2),
            "stop_loss":     round(stop_loss, 2),
            "t1":            round(target, 2),
            "rr":            rr,
            "thesis":        thesis,
        }
    except Exception as e:
        return None

def fetch_market_health():
    try:
        df = yf.Ticker("^NSEI").history(period="3mo", interval="1d", auto_adjust=True)
        c = df["Close"].values
        price = c[-1]
        ema50 = np.mean(c[-50:])
        pct = round((c[-1] - c[-2]) / c[-2] * 100, 2)
        
        status = "BULL MARKET" if price > ema50 else "CAUTION (Below 50 EMA)"
        return {"price": round(price, 2), "pct": pct, "status": status}
    except:
        return {"price": 0, "pct": 0, "status": "UNKNOWN"}

# ─────────────────────────────────────────────
# HISTORY TRACKING
# ─────────────────────────────────────────────
HISTORY_FILE = '/tmp/history.json' if 'VERCEL' in os.environ else 'history.json'

def save_to_history(scan_time, scanned, found, picks, nifty):
    try:
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        # Don't save if there are no picks
        if not picks:
            return
            
        record = {
            "scan_time": scan_time,
            "scanned": scanned,
            "found": found,
            "picks": picks,
            "nifty50": nifty
        }
        
        if history and history[0].get("scan_time") == scan_time:
            history[0] = record
        else:
            history.insert(0, record)
            
        history = history[:50]
        
        # Ensure directory exists (e.g. /tmp on Vercel)
        os.makedirs(os.path.dirname(os.path.abspath(HISTORY_FILE)), exist_ok=True)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

# ─────────────────────────────────────────────
# CACHE SYSTEM (1-Hour Cache for Vercel stability)
# ─────────────────────────────────────────────
SCAN_CACHE = None
CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # Cache for 1 hour

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────
@app.route('/api/scan', methods=['GET'])
def run_scan():
    global SCAN_CACHE, CACHE_TIMESTAMP
    t0 = time.time()
    
    # Check cache to avoid Vercel timeouts and rate-limiting
    if SCAN_CACHE and (t0 - CACHE_TIMESTAMP < CACHE_DURATION):
        return jsonify(SCAN_CACHE)

    results = []

    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(analyze_confluence, s): s for s in UNIVERSE}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # Sort deterministically by Score DESC, then RSI ASC, then Symbol alphabetically
    results.sort(key=lambda x: (-x["score"], x["rsi"], x["sym"]))
    top3 = results[:3]

    nifty = fetch_market_health()
    elapsed = round(time.time() - t0, 1)
    scan_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Save run to daily history file
    save_to_history(scan_time, len(UNIVERSE), len(results), top3, nifty)

    response_data = {
        "status": "success",
        "scan_time": scan_time,
        "elapsed": elapsed,
        "scanned": len(UNIVERSE),
        "found": len(results),
        "nifty50": nifty,
        "picks": top3,
    }

    # Update cache
    SCAN_CACHE = response_data
    CACHE_TIMESTAMP = time.time()

    return jsonify(response_data)

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
            return jsonify(history)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return jsonify({"status": "success", "message": "History cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("High Win-Rate Scanner API — Starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
