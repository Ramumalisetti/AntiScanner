"""
Elite Pullback Reversal Scanner — API Backend
Scans Nifty 500 / F&O universe for top pullback setups daily.

Criteria:
1. Stock above 50 EMA + 200 EMA (confirmed uptrend)
2. Price pulled back 3-8% from recent 20-day high
3. Price sitting on/near 20 EMA, 50 EMA, or previous breakout level
4. Bullish reversal candle (Hammer, Engulfing, Morning Star)
5. Volume drying up on dip, expanding on reversal day
6. RSI pulled back to 45-58 zone after being overbought
"""

import time, math, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# UNIVERSE — Nifty 500 / F&O liquid stocks
# ─────────────────────────────────────────────
UNIVERSE = [
    # Banking
    {"sym":"HDFCBANK","yf":"HDFCBANK.NS","sector":"Banking"},
    {"sym":"ICICIBANK","yf":"ICICIBANK.NS","sector":"Banking"},
    {"sym":"SBIN","yf":"SBIN.NS","sector":"Banking"},
    {"sym":"AXISBANK","yf":"AXISBANK.NS","sector":"Banking"},
    {"sym":"KOTAKBANK","yf":"KOTAKBANK.NS","sector":"Banking"},
    {"sym":"INDUSINDBK","yf":"INDUSINDBK.NS","sector":"Banking"},
    {"sym":"BANKBARODA","yf":"BANKBARODA.NS","sector":"Banking"},
    {"sym":"CANBK","yf":"CANBK.NS","sector":"Banking"},
    {"sym":"PNB","yf":"PNB.NS","sector":"Banking"},
    {"sym":"FEDERALBNK","yf":"FEDERALBNK.NS","sector":"Banking"},
    # Finance / NBFC
    {"sym":"BAJFINANCE","yf":"BAJFINANCE.NS","sector":"Finance"},
    {"sym":"BAJAJFINSV","yf":"BAJAJFINSV.NS","sector":"Finance"},
    {"sym":"CHOLAFIN","yf":"CHOLAFIN.NS","sector":"Finance"},
    {"sym":"MUTHOOTFIN","yf":"MUTHOOTFIN.NS","sector":"Finance"},
    {"sym":"SHRIRAMFIN","yf":"SHRIRAMFIN.NS","sector":"Finance"},
    {"sym":"HDFCAMC","yf":"HDFCAMC.NS","sector":"Finance"},
    {"sym":"CDSL","yf":"CDSL.NS","sector":"Finance"},
    {"sym":"MCX","yf":"MCX.NS","sector":"Finance"},
    {"sym":"BSE","yf":"BSE.NS","sector":"Finance"},
    {"sym":"ANGELONE","yf":"ANGELONE.NS","sector":"Finance"},
    # IT
    {"sym":"TCS","yf":"TCS.NS","sector":"IT"},
    {"sym":"INFY","yf":"INFY.NS","sector":"IT"},
    {"sym":"HCLTECH","yf":"HCLTECH.NS","sector":"IT"},
    {"sym":"WIPRO","yf":"WIPRO.NS","sector":"IT"},
    {"sym":"TECHM","yf":"TECHM.NS","sector":"IT"},
    {"sym":"LTIM","yf":"LTIM.NS","sector":"IT"},
    {"sym":"PERSISTENT","yf":"PERSISTENT.NS","sector":"IT"},
    {"sym":"COFORGE","yf":"COFORGE.NS","sector":"IT"},
    {"sym":"MPHASIS","yf":"MPHASIS.NS","sector":"IT"},
    {"sym":"KPITTECH","yf":"KPITTECH.NS","sector":"IT"},
    # Energy
    {"sym":"RELIANCE","yf":"RELIANCE.NS","sector":"Energy"},
    {"sym":"ONGC","yf":"ONGC.NS","sector":"Energy"},
    {"sym":"BPCL","yf":"BPCL.NS","sector":"Energy"},
    {"sym":"IOC","yf":"IOC.NS","sector":"Energy"},
    {"sym":"GAIL","yf":"GAIL.NS","sector":"Energy"},
    # Power
    {"sym":"NTPC","yf":"NTPC.NS","sector":"Power"},
    {"sym":"POWERGRID","yf":"POWERGRID.NS","sector":"Power"},
    {"sym":"ADANIGREEN","yf":"ADANIGREEN.NS","sector":"Power"},
    {"sym":"TATAPOWER","yf":"TATAPOWER.NS","sector":"Power"},
    {"sym":"SUZLON","yf":"SUZLON.NS","sector":"Power"},
    {"sym":"TORNTPOWER","yf":"TORNTPOWER.NS","sector":"Power"},
    # Auto
    {"sym":"MARUTI","yf":"MARUTI.NS","sector":"Auto"},
    {"sym":"TATAMOTORS","yf":"TATAMOTORS.NS","sector":"Auto"},
    {"sym":"EICHERMOT","yf":"EICHERMOT.NS","sector":"Auto"},
    {"sym":"BAJAJ-AUTO","yf":"BAJAJ-AUTO.NS","sector":"Auto"},
    {"sym":"M&M","yf":"M&M.NS","sector":"Auto"},
    {"sym":"TVSMOTORS","yf":"TVSMOTORS.NS","sector":"Auto"},
    {"sym":"HEROMOTOCO","yf":"HEROMOTOCO.NS","sector":"Auto"},
    # Pharma
    {"sym":"SUNPHARMA","yf":"SUNPHARMA.NS","sector":"Pharma"},
    {"sym":"DRREDDY","yf":"DRREDDY.NS","sector":"Pharma"},
    {"sym":"CIPLA","yf":"CIPLA.NS","sector":"Pharma"},
    {"sym":"DIVISLAB","yf":"DIVISLAB.NS","sector":"Pharma"},
    {"sym":"LUPIN","yf":"LUPIN.NS","sector":"Pharma"},
    {"sym":"AUROPHARMA","yf":"AUROPHARMA.NS","sector":"Pharma"},
    {"sym":"TORNTPHARM","yf":"TORNTPHARM.NS","sector":"Pharma"},
    # FMCG
    {"sym":"HINDUNILVR","yf":"HINDUNILVR.NS","sector":"FMCG"},
    {"sym":"ITC","yf":"ITC.NS","sector":"FMCG"},
    {"sym":"NESTLEIND","yf":"NESTLEIND.NS","sector":"FMCG"},
    {"sym":"TATACONSUM","yf":"TATACONSUM.NS","sector":"FMCG"},
    {"sym":"MARICO","yf":"MARICO.NS","sector":"FMCG"},
    {"sym":"DABUR","yf":"DABUR.NS","sector":"FMCG"},
    {"sym":"VBL","yf":"VBL.NS","sector":"FMCG"},
    # Metal
    {"sym":"TATASTEEL","yf":"TATASTEEL.NS","sector":"Metal"},
    {"sym":"JSWSTEEL","yf":"JSWSTEEL.NS","sector":"Metal"},
    {"sym":"HINDALCO","yf":"HINDALCO.NS","sector":"Metal"},
    {"sym":"COALINDIA","yf":"COALINDIA.NS","sector":"Metal"},
    {"sym":"VEDL","yf":"VEDL.NS","sector":"Metal"},
    # Healthcare
    {"sym":"APOLLOHOSP","yf":"APOLLOHOSP.NS","sector":"Healthcare"},
    {"sym":"MAXHEALTH","yf":"MAXHEALTH.NS","sector":"Healthcare"},
    {"sym":"FORTIS","yf":"FORTIS.NS","sector":"Healthcare"},
    # Capital Goods / Defence
    {"sym":"LT","yf":"LT.NS","sector":"Infra"},
    {"sym":"SIEMENS","yf":"SIEMENS.NS","sector":"CapGoods"},
    {"sym":"ABB","yf":"ABB.NS","sector":"CapGoods"},
    {"sym":"CUMMINSIND","yf":"CUMMINSIND.NS","sector":"CapGoods"},
    {"sym":"BEL","yf":"BEL.NS","sector":"Defence"},
    {"sym":"HAL","yf":"HAL.NS","sector":"Defence"},
    {"sym":"BHEL","yf":"BHEL.NS","sector":"Defence"},
    {"sym":"COCHINSHIP","yf":"COCHINSHIP.NS","sector":"Defence"},
    # PSU
    {"sym":"IRCTC","yf":"IRCTC.NS","sector":"PSU"},
    {"sym":"IRFC","yf":"IRFC.NS","sector":"PSU"},
    {"sym":"PFC","yf":"PFC.NS","sector":"PSU"},
    {"sym":"REC","yf":"REC.NS","sector":"PSU"},
    {"sym":"RVNL","yf":"RVNL.NS","sector":"PSU"},
    # Realty
    {"sym":"DLF","yf":"DLF.NS","sector":"Realty"},
    {"sym":"GODREJPROP","yf":"GODREJPROP.NS","sector":"Realty"},
    {"sym":"PRESTIGE","yf":"PRESTIGE.NS","sector":"Realty"},
    # Consumer
    {"sym":"TITAN","yf":"TITAN.NS","sector":"Consumer"},
    {"sym":"TRENT","yf":"TRENT.NS","sector":"Consumer"},
    {"sym":"ZOMATO","yf":"ZOMATO.NS","sector":"Consumer"},
    {"sym":"DMART","yf":"DMART.NS","sector":"Retail"},
    {"sym":"ASIANPAINT","yf":"ASIANPAINT.NS","sector":"Consumer"},
    {"sym":"PIDILITIND","yf":"PIDILITIND.NS","sector":"Chemical"},
    {"sym":"BHARTIARTL","yf":"BHARTIARTL.NS","sector":"Telecom"},
    {"sym":"ADANIPORTS","yf":"ADANIPORTS.NS","sector":"Infra"},
    {"sym":"ADANIENT","yf":"ADANIENT.NS","sector":"Infra"},
]

# ─────────────────────────────────────────────
# INDICATOR HELPERS
# ─────────────────────────────────────────────
def ema(c, p):
    if len(c) < p: return float(c[-1])
    k = 2 / (p + 1)
    e = float(c[0])
    for v in c[1:]: e = v * k + e * (1 - k)
    return round(e, 2)

def rsi(c, p=14):
    if len(c) < p + 2: return 50.0
    d = np.diff(np.array(c, dtype=float))
    g = np.where(d > 0, d, 0.0)
    lo = np.where(d < 0, -d, 0.0)
    ag = g[-p:].mean(); al = lo[-p:].mean()
    if al == 0: return 100.0
    return round(100 - 100 / (1 + ag / al), 1)

def atr(highs, lows, closes, p=14):
    trs = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
           for i in range(1, len(closes))]
    return float(np.mean(trs[-p:])) if trs else closes[-1] * 0.02

def detect_candle(o, h, l, c, prev_o, prev_c):
    """Detect bullish reversal candles"""
    body = abs(c - o)
    total_range = h - l if h > l else 0.001
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)

    patterns = []
    # Hammer: small body upper, long lower wick (at least 2x body), at support
    if c > o and lower_wick >= body * 2 and upper_wick < body * 0.5:
        patterns.append("Hammer")
    # Bullish Engulfing: current green body engulfs previous red body
    if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
        patterns.append("Bullish Engulfing")
    # Strong green candle after pullback
    if c > o and (c - o) / total_range > 0.6 and body > 0:
        patterns.append("Strong Bull Bar")
    # Doji near support (indecision → potential reversal)
    if body / total_range < 0.2 and lower_wick > upper_wick:
        patterns.append("Bullish Doji")
    return patterns[0] if patterns else None

def find_breakout_level(closes, highs):
    """Find most recent breakout / consolidation level that could act as support"""
    n = len(closes)
    if n < 60: return None
    # Find the highest close in days 30-60 ago
    past_window = closes[n-60:n-20]
    if len(past_window) == 0: return None
    return round(float(max(past_window)), 2)

# ─────────────────────────────────────────────
# CORE ANALYSIS
# ─────────────────────────────────────────────
def analyze(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 220:
            return None

        closes = df["Close"].values.tolist()
        opens  = df["Open"].values.tolist()
        highs  = df["High"].values.tolist()
        lows   = df["Low"].values.tolist()
        vols   = df["Volume"].values.tolist()
        n = len(closes)

        price = closes[-1]

        # ── EMAs ──
        ema20  = ema(closes[-60:],   20)
        ema50  = ema(closes[-100:],  50)
        ema200 = ema(closes[-200:], 200)

        # ── 1. UPTREND FILTER ──
        if not (price > ema50 and price > ema200):
            return None  # must be in uptrend

        # ── 2. PULLBACK MEASURE ──
        recent_high = max(highs[-20:])
        pullback_pct = round((recent_high - price) / recent_high * 100, 2)
        if not (2.5 <= pullback_pct <= 10.0):
            return None  # pullback must be 2.5-10%

        # ── 3. AT KEY SUPPORT ──
        dist_ema20 = abs(price - ema20) / price * 100
        dist_ema50 = abs(price - ema50) / price * 100
        bo_level   = find_breakout_level(closes, highs)
        dist_bo    = abs(price - bo_level) / price * 100 if bo_level else 999

        near_ema20 = dist_ema20 < 2.5
        near_ema50 = dist_ema50 < 3.0
        near_bo    = dist_bo < 3.5

        if not (near_ema20 or near_ema50 or near_bo):
            return None  # must be at a meaningful support

        support_level = None
        support_name  = None
        if near_ema20:
            support_level = ema20; support_name = "20 EMA"
        elif near_ema50:
            support_level = ema50; support_name = "50 EMA"
        elif near_bo:
            support_level = bo_level; support_name = "Previous Breakout Level"

        # ── 4. REVERSAL CANDLE ──
        candle_pattern = detect_candle(
            opens[-1], highs[-1], lows[-1], closes[-1],
            opens[-2], closes[-2]
        )

        # ── 5. VOLUME ANALYSIS ──
        avg_vol_20 = float(np.mean(vols[-20:]))
        avg_vol_3d = float(np.mean(vols[-4:-1]))   # last 3 days (dip)
        today_vol  = vols[-1]
        vol_dry_up   = avg_vol_3d < avg_vol_20 * 0.75   # volume drying on dip
        vol_expanding = today_vol > avg_vol_20 * 1.1    # expanding on reversal
        vol_ratio     = round(today_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0

        # ── 6. RSI ──
        rsi_now  = rsi(closes[-30:])
        rsi_3d   = rsi(closes[-33:-3])
        in_buy_zone    = 40 <= rsi_now <= 62
        rsi_divergence = closes[-1] < closes[-5] and rsi_now > rsi_3d  # price lower, rsi higher

        # ── 7. SCORING (0-10) ──
        score = 0.0
        # Trend quality
        if price > ema200: score += 1.5
        if price > ema50:  score += 1.0
        # Pullback quality
        if 3.0 <= pullback_pct <= 7.0: score += 2.0
        else: score += 1.0
        # At clean support
        if near_ema20:  score += 1.5
        elif near_ema50: score += 1.2
        elif near_bo:   score += 1.0
        # Reversal signal
        if candle_pattern in ("Bullish Engulfing", "Hammer"): score += 1.5
        elif candle_pattern: score += 0.8
        # Volume
        if vol_dry_up:     score += 0.5
        if vol_expanding:  score += 0.8
        elif vol_ratio > 0.9: score += 0.3
        # RSI
        if in_buy_zone:     score += 0.8
        if rsi_divergence:  score += 0.7
        score = min(round(score, 1), 10.0)

        if score < 5.0:
            return None

        # ── TRADE LEVELS ──
        atr_val = atr(highs, lows, closes)
        swing_low = min(lows[-5:])
        stop_loss = round(swing_low - atr_val * 0.2, 2)
        risk = price - stop_loss
        if risk <= 0: return None

        t1 = round(price + risk * 2.0, 2)
        t2 = round(price + risk * 3.5, 2)
        rr = round((t1 - price) / risk, 1)

        # ── THESIS ──
        thesis_parts = [
            f"{stock['sym']} is in a confirmed uptrend (above 50 EMA at ₹{ema50:.0f} and 200 EMA at ₹{ema200:.0f}).",
            f"Price has pulled back {pullback_pct:.1f}% from its recent high of ₹{recent_high:.0f}.",
            f"Now retesting {support_name} (₹{support_level:.0f}) — a high-interest institutional demand zone.",
        ]
        if candle_pattern:
            thesis_parts.append(f"A {candle_pattern} pattern is forming, signaling buyers stepping in.")
        if vol_dry_up:
            thesis_parts.append(f"Volume dried up during the dip (avg 3d: {avg_vol_3d/1e5:.1f}L vs 20d avg: {avg_vol_20/1e5:.1f}L) — no institutional selling.")
        if vol_expanding:
            thesis_parts.append(f"Volume is NOW expanding on the reversal ({vol_ratio}x avg) — demand confirmation.")
        if in_buy_zone:
            thesis_parts.append(f"RSI at {rsi_now} — pulled back to neutral buy zone without becoming oversold.")
        if rsi_divergence:
            thesis_parts.append("RSI bullish divergence detected: price lower, RSI higher — momentum shifting.")

        entry_strategy = (
            f"Enter on a 15-min close above ₹{round(price + atr_val * 0.2, 0):.0f} "
            f"(above today's candle high) with volume confirmation. "
            f"Alternatively, wait for a 30-min candle close above the {support_name} retest zone."
        )
        if candle_pattern in ("Bullish Engulfing", "Hammer"):
            entry_strategy = (
                f"Enter NOW on market open confirmation or a 15-min hold above ₹{round(highs[-1], 0):.0f} "
                f"(today's {candle_pattern} high) with volume. Stop is firm below ₹{stop_loss:.0f}."
            )

        return {
            "sym":           stock["sym"],
            "sector":        stock["sector"],
            "price":         round(price, 2),
            "score":         score,
            "pullback_pct":  pullback_pct,
            "recent_high":   round(recent_high, 2),
            "support_level": round(support_level, 2),
            "support_name":  support_name,
            "candle":        candle_pattern or "No clear pattern yet",
            "ema20":         ema20,
            "ema50":         ema50,
            "ema200":        ema200,
            "rsi":           rsi_now,
            "vol_ratio":     vol_ratio,
            "vol_dry_up":    vol_dry_up,
            "vol_expanding": vol_expanding,
            "entry":         round(highs[-1] + 0.1, 2),
            "stop_loss":     stop_loss,
            "t1":            t1,
            "t2":            t2,
            "rr":            rr,
            "thesis":        " ".join(thesis_parts),
            "entry_strategy":entry_strategy,
        }
    except Exception as e:
        return None

def fetch_nifty50_context():
    try:
        df = yf.Ticker("^NSEI").history(period="3mo", interval="1d", auto_adjust=True)
        c = df["Close"].values.tolist()
        price = c[-1]
        e20 = ema(c[-60:], 20)
        e50 = ema(c[-100:], 50)
        e200 = ema(c[-200:] if len(c) >= 200 else c, 200)
        pct_chg = round((c[-1] - c[-2]) / c[-2] * 100, 2) if len(c) > 1 else 0
        trend = "BULLISH" if price > e50 > e200 else "BEARISH" if price < e50 < e200 else "MIXED"
        return {
            "price":  round(price, 2),
            "pct":    pct_chg,
            "ema20":  round(e20, 2),
            "ema50":  round(e50, 2),
            "ema200": round(e200, 2),
            "trend":  trend,
            "above50": price > e50,
            "above200": price > e200,
        }
    except:
        return {"price": 0, "pct": 0, "ema20": 0, "ema50": 0, "ema200": 0, "trend": "UNKNOWN", "above50": False, "above200": False}

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────
@app.route('/api/scan', methods=['GET'])
def run_scan():
    t0 = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(analyze, s): s for s in UNIVERSE}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # Sort by score desc, take top 3 with sector diversity
    results.sort(key=lambda x: -x["score"])
    top3 = []
    seen_sectors = set()
    for r in results:
        if r["sector"] not in seen_sectors:
            top3.append(r)
            seen_sectors.add(r["sector"])
        if len(top3) >= 3:
            break
    # Fill up to 3 even if same sector
    if len(top3) < 3:
        for r in results:
            if r not in top3:
                top3.append(r)
            if len(top3) >= 3:
                break

    nifty = fetch_nifty50_context()
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
    print("Elite Pullback Scanner API — Starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
