"""
High-Probability Confluence Scanner — API Backend
Targeting >70% Win Rate.
Blends SMC Demand Zones with Classic Mean Reversion (RSI, EMA, ATR).
Exposes additional analyst strategies: "Hold with Priyank" & "DarvaX AmitabhJha3".
"""

import time, math, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np
import pandas as pd

# Add current path to import local scanners
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from priyank_scanner import priyank_analyze
except Exception as e:
    print(f"Failed to import priyank_scanner: {e}")
    priyank_analyze = None

try:
    from darvax_scanner import analyze as darvax_analyze
except Exception as e:
    print(f"Failed to import darvax_scanner: {e}")
    darvax_analyze = None

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
# CONFLUENCE ANALYSIS LOGIC
# ─────────────────────────────────────────────
def analyze_confluence_logic(df, stock):
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

# ─────────────────────────────────────────────
# UNIFIED MULTI-STRATEGY ANALYSIS WORKER
# ─────────────────────────────────────────────
def analyze_stock_all_strategies(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 100:
            return None

        # 1. Confluence Scanner
        confluence_res = None
        if len(df) >= 200:
            confluence_res = analyze_confluence_logic(df, stock)

        # Convert to lowercase columns for other strategies
        df_lower = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df_lower.columns = ["open", "high", "low", "close", "volume"]

        # 2. Priyank Strategy
        priyank_res = None
        if priyank_analyze:
            try:
                pa = priyank_analyze(df_lower, stock)
                if pa and pa.get("trade") and pa.get("score", 0) >= 15:
                    pa["sym"] = stock["sym"]
                    pa["sector"] = stock["sector"]
                    priyank_res = pa
            except Exception as e:
                pass

        # 3. Darvax Strategy
        darvax_res = None
        if darvax_analyze:
            try:
                da = darvax_analyze(df_lower, stock)
                if da and da.get("trade") and da.get("score", 0) >= 15:
                    da["sym"] = stock["sym"]
                    da["sector"] = stock["sector"]
                    darvax_res = da
            except Exception as e:
                pass

        return {
            "sym": stock["sym"],
            "sector": stock["sector"],
            "confluence": confluence_res,
            "priyank": priyank_res,
            "darvax": darvax_res
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
# NATIVE PYTHON SERIALIZATION CONVERTER
# ─────────────────────────────────────────────
def convert_numpy(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy(obj.tolist())
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (bool, int, float, str)) or obj is None:
        return obj
    else:
        try:
            if hasattr(obj, 'item'):
                return obj.item()
        except:
            pass
        return obj

# ─────────────────────────────────────────────
# HISTORY TRACKING
# ─────────────────────────────────────────────
HISTORY_FILE = '/tmp/history.json' if 'VERCEL' in os.environ else 'history.json'

def save_to_history(scan_time, scanned, found, picks, nifty, priyank_pick=None, darvax_pick=None):
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
            "nifty50": nifty,
            "priyank_pick": priyank_pick,
            "darvax_pick": darvax_pick
        }
        
        if history and history[0].get("scan_time") == scan_time:
            history[0] = record
        else:
            history.insert(0, record)
            
        history = history[:50]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(HISTORY_FILE)), exist_ok=True)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

# ─────────────────────────────────────────────
# CACHE SYSTEM (1-Hour Cache)
# ─────────────────────────────────────────────
SCAN_CACHE = None
CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600

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

    confluence_results = []
    priyank_results = []
    darvax_results = []

    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(analyze_stock_all_strategies, s): s for s in UNIVERSE}
        for f in as_completed(futures):
            r = f.result()
            if r:
                if r["confluence"]:
                    confluence_results.append(r["confluence"])
                if r["priyank"]:
                    priyank_results.append(r["priyank"])
                if r["darvax"]:
                    darvax_results.append(r["darvax"])

    # 1. Confluence Picks (Top 3)
    confluence_results.sort(key=lambda x: (-x["score"], x["rsi"], x["sym"]))
    top3_confluence = confluence_results[:3]

    # 2. Priyank Pick (Best 1)
    priyank_results.sort(key=lambda x: (-x["score"], -x["vol_ratio"], x["sym"]))
    best_priyank = priyank_results[0] if priyank_results else None

    # 3. Darvax Pick (Best 1)
    darvax_results.sort(key=lambda x: (-x["score"], -x["vr"], x["sym"]))
    best_darvax = darvax_results[0] if darvax_results else None

    nifty = fetch_market_health()
    elapsed = round(time.time() - t0, 1)
    scan_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

    response_data = {
        "status": "success",
        "scan_time": scan_time,
        "elapsed": elapsed,
        "scanned": len(UNIVERSE),
        "found": len(confluence_results),
        "nifty50": nifty,
        "picks": top3_confluence,
        "priyank_pick": best_priyank,
        "darvax_pick": best_darvax,
    }

    # Recursive conversion of NumPy types to make them JSON serializable
    response_data = convert_numpy(response_data)

    # Save run to daily history file
    save_to_history(
        response_data["scan_time"], 
        response_data["scanned"], 
        response_data["found"], 
        response_data["picks"], 
        response_data["nifty50"], 
        response_data["priyank_pick"], 
        response_data["darvax_pick"]
    )

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
