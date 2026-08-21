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

import threading

# Isolate yfinance cache per process AND per thread to prevent SQLite "database is locked" errors during high concurrency
try:
    yf.set_tz_cache_location(":memory:")
except Exception:
    pass

# Ensure local directory is in sys.path so Vercel can import sibling modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
import traceback
import_errors = {}

try:
    from psbb_scanner import psbb_analyze
    priyank_analyze = True
except Exception as e:
    import_errors['psbb'] = traceback.format_exc()
    psbb_analyze = None
    priyank_analyze = None

try:
    from darvax_scanner import analyze as darvax_analyze
except Exception as e:
    import_errors['darvax'] = traceback.format_exc()
    darvax_analyze = None

try:
    from bos_choch_scanner import live_scan_from_df as boschoch_analyze
except Exception as e:
    import_errors['boschoch'] = traceback.format_exc()
    boschoch_analyze = None

# Initialize Flask to serve static files from the 'static' directory
app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)

# Serve the React frontend for the root route and any unmatched routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    import os
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')

def clean_numpy(obj):
    if isinstance(obj, (np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: clean_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_numpy(v) for v in obj]
    return obj

# ─────────────────────────────────────────────
# UNIVERSE
# ─────────────────────────────────────────────
UNIVERSE = []
universe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'universe.json')
if os.path.exists(universe_path):
    with open(universe_path, 'r') as f:
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

def save_to_history(scan_time, scanned, found, picks, nifty, strategy="confluence"):
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
            "strategy": strategy,
            "scanned": scanned,
            "found": found,
            "picks": picks,
            "nifty50": nifty,
        }
        
        history.insert(0, record)
        history = history[:100]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(HISTORY_FILE)), exist_ok=True)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

# ─────────────────────────────────────────────
# INDIVIDUAL STRATEGY WORKERS
# ─────────────────────────────────────────────
def analyze_confluence_worker(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 200:
            return None
        return analyze_confluence_logic(df, stock)
    except:
        return None

def analyze_priyank_worker(stock):
    """PSBB — Priyank Sharma Bread & Butter scanner.
    Uses SMC: FVG, Order Block, BOS market structure, RSI divergence, 21 EMA.
    """
    if not psbb_analyze:
        return None
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 50:
            return None

        df_lower = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df_lower.columns = ["open", "high", "low", "close", "volume"]

        result = psbb_analyze(df_lower, stock)
        if result and result.get("score", 0) >= 10:  # min 1 confluence factor
            result["sym"] = stock["sym"]
            result["sector"] = stock["sector"]
            result["price"] = result.get("entry", df_lower["close"].iloc[-1])
            return result
    except Exception as e:
        import traceback
        return {"error": True, "msg": traceback.format_exc()}
    return None

def analyze_darvax_worker(stock):
    if not darvax_analyze:
        return None
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 60:
            return None
        df_lower = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df_lower.columns = ["open", "high", "low", "close", "volume"]
        da = darvax_analyze(df_lower, stock)
        # DarvaX: accept any setup with score>=20, even if trade is not set yet
        if da and da.get("score", 0) >= 20:
            if not da.get("trade"):
                price = da.get("price", 0)
                atr = da.get("atr", price * 0.02)
                bc_ceil = da.get("box_ceil")
                bc_floor = da.get("box_floor")
                entry = round((bc_ceil or price) * 1.001, 2)
                sl = round(bc_floor or (price - 2 * atr), 2)
                risk = max(entry - sl, price * 0.02)
                da["trade"] = {
                    "entry": entry, "sl": sl, "sl_pct": round((entry - sl) / entry * 100, 1),
                    "t1": round(entry + risk, 2), "t2": round(entry + risk * 2, 2),
                    "t3": round(entry + risk * 3.5, 2),
                    "rr1": round(risk / max(entry - sl, 0.01), 1),
                    "rr2": round(risk * 2 / max(entry - sl, 0.01), 1),
                    "timing": f"Watch for breakout above ₹{bc_ceil or entry:.0f} with high volume",
                    "ema10": da.get("ema10", price), "ema20": da.get("ema20", price),
                    "ema200": da.get("ema200", price)
                }
            da["sym"] = stock["sym"]
            da["sector"] = stock["sector"]
            return da
    except Exception as e:
        import traceback
        return {"error": True, "msg": traceback.format_exc()}
    return None

def _boschoch_worker(stock, setup_filter):
    """Generic BOS CHOCH worker helper."""
    if not boschoch_analyze:
        return None
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 100:
            return None
        bc = boschoch_analyze(df, stock["sym"], setup_filter=setup_filter)
        if bc and len(bc) > 0:
            setup = sorted(bc, key=lambda x: x.get("BOS Strength Score", 0), reverse=True)[0]
            return {
                "sym": stock["sym"],
                "sector": stock["sector"],
                "trade": "BUY" if setup.get("Setup Type") == "LONG" else "SELL",
                "price": setup.get("Entry"),
                "entry": setup.get("Entry"),
                "sl": setup.get("Stop Loss"),
                "t1": setup.get("Target 1R"),
                "t2": setup.get("Target 2R"),
                "setup_direction": setup.get("Setup Type"),
                "score": int(setup.get("BOS Strength Score", 0) * 10),
                "desc": f"BOS CHOCH {setup.get('Setup Type')} — SL: {setup.get('Stop Loss')}",
                "thesis": f"Entry: {setup.get('Entry')} | Risk: {setup.get('Risk %')}% | T1: {setup.get('Target 1R')} | T2: {setup.get('Target 2R')} | Vol: {setup.get('Volume Ratio')}x avg"
            }
    except Exception as e:
        import traceback
        return {"error": True, "msg": traceback.format_exc()}
    return None

def analyze_boschoch_bull_worker(stock):
    """BOS CHOCH BULL — Bullish Reversal (LONG setups only)."""
    return _boschoch_worker(stock, 'LONG')

def analyze_boschoch_bear_worker(stock):
    """BOS CHOCH BEAR — Bearish Reversal (SHORT setups only)."""
    return _boschoch_worker(stock, 'SHORT')

# ─────────────────────────────────────────────
# CACHES (per strategy)
# ─────────────────────────────────────────────
CACHES = {
    "confluence":    {"data": None, "ts": 0},
    "priyank":       {"data": None, "ts": 0},
    "darvax":        {"data": None, "ts": 0},
    "boschoch_bull": {"data": None, "ts": 0},
    "boschoch_bear": {"data": None, "ts": 0},
}
CACHE_DURATION = 0  # Disabled for live testing

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────
@app.route('/api/scan', methods=['GET'])
def run_scan():
    from flask import request
    strategy = request.args.get('strategy', 'confluence')
    # Batch/chunk support: frontend sends start + limit to scan a slice
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', len(UNIVERSE)))
    t0 = time.time()

    # Slice the universe for this chunk
    chunk = UNIVERSE[start: start + limit]

    # Only use cache for full scans (no start/limit passed)
    is_full_scan = (start == 0 and limit >= len(UNIVERSE))
    cache = CACHES.get(strategy, CACHES["confluence"])
    if is_full_scan and cache["data"] and (t0 - cache["ts"] < CACHE_DURATION):
        return jsonify(cache["data"])

    nifty = fetch_market_health()
    scan_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

    if strategy == "confluence":
        results = []
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = {ex.submit(analyze_confluence_worker, s): s for s in chunk}
            for f in as_completed(futures):
                r = f.result()
                if r:
                    results.append(r)
        results.sort(key=lambda x: (-x["score"], x["rsi"], x["sym"]))
        top_picks = results
        elapsed = round(time.time() - t0, 1)
        response_data = {
            "status": "success",
            "strategy": "confluence",
            "scan_time": scan_time,
            "elapsed": elapsed,
            "scanned": len(chunk),
            "found": len(results),
            "nifty50": nifty,
            "picks": top_picks,
        }
        return jsonify(clean_numpy(response_data))

    elif strategy == "priyank":
        if not psbb_analyze:
            return jsonify({"status": "error", "message": "PSBB Import Failed", "trace": import_errors.get('psbb')}), 500
        results = []
        errors = []
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = {ex.submit(analyze_priyank_worker, s): s for s in chunk}
            for f in as_completed(futures):
                r = f.result()
                if r:
                    if r.get("error"):
                        errors.append(r["msg"])
                    else:
                        results.append(r)
        
        if errors and not results:
            return jsonify({"status": "error", "message": "Execution Error", "trace": errors[0]}), 500
            
        results.sort(key=lambda x: (-x["score"], -x["vol_ratio"], x["sym"]))
        top_picks = results
        elapsed = round(time.time() - t0, 1)
        response_data = {
            "status": "success",
            "strategy": "priyank",
            "scan_time": scan_time,
            "elapsed": elapsed,
            "scanned": len(chunk),
            "found": len(results),
            "nifty50": nifty,
            "picks": top_picks,
        }
        return jsonify(clean_numpy(response_data))

    elif strategy == "darvax":
        if not darvax_analyze:
            return jsonify({"status": "error", "message": "DarvaX Import Failed", "trace": import_errors.get('darvax')}), 500
        results = []
        errors = []
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = {ex.submit(analyze_darvax_worker, s): s for s in chunk}
            for f in as_completed(futures):
                r = f.result()
                if r:
                    if r.get("error"):
                        errors.append(r["msg"])
                    else:
                        results.append(r)
        
        if errors and not results:
            return jsonify({"status": "error", "message": "Execution Error", "trace": errors[0]}), 500
            
        results.sort(key=lambda x: (-x["score"], -x.get("vr", 0), x["sym"]))
        top_picks = results
        elapsed = round(time.time() - t0, 1)
        response_data = {
            "status": "success",
            "strategy": "darvax",
            "scan_time": scan_time,
            "elapsed": elapsed,
            "scanned": len(chunk),
            "found": len(results),
            "nifty50": nifty,
            "picks": top_picks,
        }
        return jsonify(clean_numpy(response_data))

    elif strategy == "boschoch_bull":
        if not boschoch_analyze:
            return jsonify({"status": "error", "message": "BOSCHOCH Import Failed", "trace": import_errors.get('boschoch')}), 500
        results = []
        errors = []
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = {ex.submit(analyze_boschoch_bull_worker, s): s for s in chunk}
            for f in as_completed(futures):
                r = f.result()
                if r:
                    if r.get("error"):
                        errors.append(r["msg"])
                    else:
                        results.append(r)
        
        if errors and not results:
            return jsonify({"status": "error", "message": "Execution Error", "trace": errors[0]}), 500
            
        results.sort(key=lambda x: (-x["score"], x["sym"]))
        top_picks = results
        elapsed = round(time.time() - t0, 1)
        response_data = {
            "status": "success",
            "strategy": "boschoch_bull",
            "scan_time": scan_time,
            "elapsed": elapsed,
            "scanned": len(chunk),
            "found": len(results),
            "nifty50": nifty,
            "picks": top_picks,
        }
        return jsonify(clean_numpy(response_data))

    elif strategy == "boschoch_bear":
        if not boschoch_analyze:
            return jsonify({"status": "error", "message": "BOSCHOCH Import Failed", "trace": import_errors.get('boschoch')}), 500
        results = []
        errors = []
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = {ex.submit(analyze_boschoch_bear_worker, s): s for s in chunk}
            for f in as_completed(futures):
                r = f.result()
                if r:
                    if r.get("error"):
                        errors.append(r["msg"])
                    else:
                        results.append(r)
        
        if errors and not results:
            return jsonify({"status": "error", "message": "Execution Error", "trace": errors[0]}), 500
            
        results.sort(key=lambda x: (-x["score"], x["sym"]))
        top_picks = results
        elapsed = round(time.time() - t0, 1)
        response_data = {
            "status": "success",
            "strategy": "boschoch_bear",
            "scan_time": scan_time,
            "elapsed": elapsed,
            "scanned": len(chunk),
            "found": len(results),
            "nifty50": nifty,
            "picks": top_picks,
        }
        return jsonify(clean_numpy(response_data))
    else:
        return jsonify({"error": "Unknown strategy"}), 400

@app.route('/api/yf_test')
def yf_test():
    import traceback
    try:
        ticker = yf.Ticker("RELIANCE.NS")
        df = ticker.history(period="1mo", interval="1d", auto_adjust=True)
        return jsonify({
            "status": "success",
            "empty": bool(df.empty),
            "length": len(df),
            "tail": df.tail(1).to_dict() if not df.empty else "None",
            "tz": str(df.index.tz) if not df.empty else "None"
        })
    except Exception as e:
        return jsonify({"status": "error", "trace": traceback.format_exc()})

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
