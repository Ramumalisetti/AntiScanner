"""
NSE F&O SMC SCANNER — Full Edition
Entry · Stop Loss · Target · Multibagger · Weekly Picks
"""

import random
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# ═══════════════════════════════════════════════════════
#  F&O STOCK UNIVERSE
# ═══════════════════════════════════════════════════════
FNO_STOCKS = [
    {"sym":"HDFCBANK",   "yf":"HDFCBANK.NS",   "sector":"Banking",  "lot":550,  "weight":6.24},
    {"sym":"ICICIBANK",  "yf":"ICICIBANK.NS",   "sector":"Banking",  "lot":700,  "weight":4.97},
    {"sym":"SBIN",       "yf":"SBIN.NS",        "sector":"Banking",  "lot":1500, "weight":5.16},
    {"sym":"AXISBANK",   "yf":"AXISBANK.NS",    "sector":"Banking",  "lot":1200, "weight":2.17},
    {"sym":"KOTAKBANK",  "yf":"KOTAKBANK.NS",   "sector":"Banking",  "lot":400,  "weight":1.95},
    {"sym":"INDUSINDBK", "yf":"INDUSINDBK.NS",  "sector":"Banking",  "lot":500,  "weight":1.10},
    {"sym":"BANKBARODA", "yf":"BANKBARODA.NS",  "sector":"Banking",  "lot":5850, "weight":0.60},
    {"sym":"PNB",        "yf":"PNB.NS",         "sector":"Banking",  "lot":8000, "weight":0.55},
    {"sym":"CANBK",      "yf":"CANBK.NS",       "sector":"Banking",  "lot":4700, "weight":0.50},
    {"sym":"IDFCFIRSTB", "yf":"IDFCFIRSTB.NS",  "sector":"Banking",  "lot":10000,"weight":0.40},
    {"sym":"FEDERALBNK", "yf":"FEDERALBNK.NS",  "sector":"Banking",  "lot":10000,"weight":0.38},
    {"sym":"BAJFINANCE", "yf":"BAJFINANCE.NS",  "sector":"Finance",  "lot":125,  "weight":2.95},
    {"sym":"BAJAJFINSV", "yf":"BAJAJFINSV.NS",  "sector":"Finance",  "lot":500,  "weight":1.65},
    {"sym":"SHRIRAMFIN", "yf":"SHRIRAMFIN.NS",  "sector":"Finance",  "lot":300,  "weight":0.72},
    {"sym":"CHOLAFIN",   "yf":"CHOLAFIN.NS",    "sector":"Finance",  "lot":500,  "weight":0.60},
    {"sym":"MUTHOOTFIN", "yf":"MUTHOOTFIN.NS",  "sector":"Finance",  "lot":750,  "weight":0.55},
    {"sym":"JIOFIN",     "yf":"JIOFIN.NS",      "sector":"Finance",  "lot":6250, "weight":0.50},
    {"sym":"CDSL",       "yf":"CDSL.NS",        "sector":"Finance",  "lot":600,  "weight":0.45},
    {"sym":"MCX",        "yf":"MCX.NS",         "sector":"Finance",  "lot":800,  "weight":0.40},
    {"sym":"ANGELONE",   "yf":"ANGELONE.NS",    "sector":"Finance",  "lot":500,  "weight":0.38},
    {"sym":"SBILIFE",    "yf":"SBILIFE.NS",     "sector":"Insurance","lot":750,  "weight":0.62},
    {"sym":"HDFCLIFE",   "yf":"HDFCLIFE.NS",    "sector":"Insurance","lot":1100, "weight":0.60},
    {"sym":"LICI",       "yf":"LICI.NS",        "sector":"Insurance","lot":700,  "weight":0.58},
    {"sym":"ICICIGI",    "yf":"ICICIGI.NS",     "sector":"Insurance","lot":375,  "weight":0.55},
    {"sym":"TCS",        "yf":"TCS.NS",         "sector":"IT",       "lot":175,  "weight":4.65},
    {"sym":"INFY",       "yf":"INFY.NS",        "sector":"IT",       "lot":400,  "weight":2.61},
    {"sym":"HCLTECH",    "yf":"HCLTECH.NS",     "sector":"IT",       "lot":700,  "weight":1.88},
    {"sym":"WIPRO",      "yf":"WIPRO.NS",       "sector":"IT",       "lot":1500, "weight":1.55},
    {"sym":"TECHM",      "yf":"TECHM.NS",       "sector":"IT",       "lot":600,  "weight":1.15},
    {"sym":"LTIM",       "yf":"LTIM.NS",        "sector":"IT",       "lot":150,  "weight":0.90},
    {"sym":"MPHASIS",    "yf":"MPHASIS.NS",     "sector":"IT",       "lot":400,  "weight":0.70},
    {"sym":"COFORGE",    "yf":"COFORGE.NS",     "sector":"IT",       "lot":150,  "weight":0.65},
    {"sym":"PERSISTENT", "yf":"PERSISTENT.NS",  "sector":"IT",       "lot":125,  "weight":0.62},
    {"sym":"OFSS",       "yf":"OFSS.NS",        "sector":"IT",       "lot":200,  "weight":0.60},
    {"sym":"KPITTECH",   "yf":"KPITTECH.NS",    "sector":"IT",       "lot":500,  "weight":0.55},
    {"sym":"RELIANCE",   "yf":"RELIANCE.NS",    "sector":"Energy",   "lot":250,  "weight":9.35},
    {"sym":"ONGC",       "yf":"ONGC.NS",        "sector":"Energy",   "lot":3850, "weight":1.50},
    {"sym":"BPCL",       "yf":"BPCL.NS",        "sector":"Energy",   "lot":1800, "weight":0.75},
    {"sym":"IOC",        "yf":"IOC.NS",         "sector":"Energy",   "lot":10500,"weight":0.68},
    {"sym":"HINDPETRO",  "yf":"HINDPETRO.NS",   "sector":"Energy",   "lot":2700, "weight":0.60},
    {"sym":"GAIL",       "yf":"GAIL.NS",        "sector":"Energy",   "lot":6850, "weight":0.58},
    {"sym":"IGL",        "yf":"IGL.NS",         "sector":"Energy",   "lot":2750, "weight":0.50},
    {"sym":"NTPC",       "yf":"NTPC.NS",        "sector":"Power",    "lot":2700, "weight":1.25},
    {"sym":"POWERGRID",  "yf":"POWERGRID.NS",   "sector":"Power",    "lot":3200, "weight":1.30},
    {"sym":"ADANIGREEN", "yf":"ADANIGREEN.NS",  "sector":"Power",    "lot":500,  "weight":0.80},
    {"sym":"ADANIPOWER", "yf":"ADANIPOWER.NS",  "sector":"Power",    "lot":2100, "weight":0.75},
    {"sym":"TATAPOWER",  "yf":"TATAPOWER.NS",   "sector":"Power",    "lot":3375, "weight":0.70},
    {"sym":"SUZLON",     "yf":"SUZLON.NS",      "sector":"Power",    "lot":14000,"weight":0.60},
    {"sym":"MARUTI",     "yf":"MARUTI.NS",      "sector":"Auto",     "lot":37,   "weight":2.13},
    {"sym":"TATAMOTORS", "yf":"TATAMOTORS.NS",  "sector":"Auto",     "lot":1400, "weight":1.28},
    {"sym":"EICHERMOT",  "yf":"EICHERMOT.NS",   "sector":"Auto",     "lot":175,  "weight":0.90},
    {"sym":"HEROMOTOCO", "yf":"HEROMOTOCO.NS",  "sector":"Auto",     "lot":300,  "weight":0.78},
    {"sym":"BAJAJ-AUTO", "yf":"BAJAJ-AUTO.NS",  "sector":"Auto",     "lot":125,  "weight":0.65},
    {"sym":"M&M",        "yf":"M&M.NS",         "sector":"Auto",     "lot":700,  "weight":1.50},
    {"sym":"TVSMOTORS",  "yf":"TVSMOTORS.NS",   "sector":"Auto",     "lot":350,  "weight":0.70},
    {"sym":"ASHOKLEY",   "yf":"ASHOKLEY.NS",    "sector":"Auto",     "lot":5500, "weight":0.55},
    {"sym":"SUNPHARMA",  "yf":"SUNPHARMA.NS",   "sector":"Pharma",   "lot":700,  "weight":1.98},
    {"sym":"DRREDDY",    "yf":"DRREDDY.NS",     "sector":"Pharma",   "lot":125,  "weight":0.95},
    {"sym":"CIPLA",      "yf":"CIPLA.NS",       "sector":"Pharma",   "lot":650,  "weight":0.98},
    {"sym":"DIVISLAB",   "yf":"DIVISLAB.NS",    "sector":"Pharma",   "lot":200,  "weight":0.92},
    {"sym":"AUROPHARMA", "yf":"AUROPHARMA.NS",  "sector":"Pharma",   "lot":650,  "weight":0.70},
    {"sym":"LUPIN",      "yf":"LUPIN.NS",       "sector":"Pharma",   "lot":425,  "weight":0.68},
    {"sym":"TORNTPHARM", "yf":"TORNTPHARM.NS",  "sector":"Pharma",   "lot":500,  "weight":0.62},
    {"sym":"ALKEM",      "yf":"ALKEM.NS",       "sector":"Pharma",   "lot":150,  "weight":0.60},
    {"sym":"APOLLOHOSP", "yf":"APOLLOHOSP.NS",  "sector":"Healthcare","lot":175, "weight":0.85},
    {"sym":"MAXHEALTH",  "yf":"MAXHEALTH.NS",   "sector":"Healthcare","lot":700, "weight":0.50},
    {"sym":"FORTIS",     "yf":"FORTIS.NS",      "sector":"Healthcare","lot":3500,"weight":0.45},
    {"sym":"TATASTEEL",  "yf":"TATASTEEL.NS",   "sector":"Metal",    "lot":5500, "weight":1.20},
    {"sym":"JSWSTEEL",   "yf":"JSWSTEEL.NS",    "sector":"Metal",    "lot":1350, "weight":1.35},
    {"sym":"HINDALCO",   "yf":"HINDALCO.NS",    "sector":"Metal",    "lot":2800, "weight":1.08},
    {"sym":"COALINDIA",  "yf":"COALINDIA.NS",   "sector":"Metal",    "lot":4200, "weight":1.02},
    {"sym":"VEDL",       "yf":"VEDL.NS",        "sector":"Metal",    "lot":2800, "weight":0.80},
    {"sym":"SAIL",       "yf":"SAIL.NS",        "sector":"Metal",    "lot":9500, "weight":0.55},
    {"sym":"NMDC",       "yf":"NMDC.NS",        "sector":"Metal",    "lot":5500, "weight":0.52},
    {"sym":"HINDUNILVR", "yf":"HINDUNILVR.NS",  "sector":"FMCG",     "lot":300,  "weight":2.82},
    {"sym":"ITC",        "yf":"ITC.NS",         "sector":"FMCG",     "lot":3200, "weight":0.68},
    {"sym":"NESTLEIND",  "yf":"NESTLEIND.NS",   "sector":"FMCG",     "lot":40,   "weight":1.40},
    {"sym":"TATACONSUM", "yf":"TATACONSUM.NS",  "sector":"FMCG",     "lot":1100, "weight":0.88},
    {"sym":"MARICO",     "yf":"MARICO.NS",      "sector":"FMCG",     "lot":2000, "weight":0.70},
    {"sym":"DABUR",      "yf":"DABUR.NS",       "sector":"FMCG",     "lot":2750, "weight":0.65},
    {"sym":"LT",         "yf":"LT.NS",          "sector":"Infra",    "lot":175,  "weight":2.80},
    {"sym":"ADANIENT",   "yf":"ADANIENT.NS",    "sector":"Infra",    "lot":1250, "weight":1.60},
    {"sym":"ADANIPORTS", "yf":"ADANIPORTS.NS",  "sector":"Infra",    "lot":1250, "weight":0.82},
    {"sym":"GMRINFRA",   "yf":"GMRINFRA.NS",    "sector":"Infra",    "lot":22500,"weight":0.55},
    {"sym":"DLF",        "yf":"DLF.NS",         "sector":"Realty",   "lot":1650, "weight":0.80},
    {"sym":"GODREJPROP", "yf":"GODREJPROP.NS",  "sector":"Realty",   "lot":650,  "weight":0.70},
    {"sym":"ULTRACEMCO", "yf":"ULTRACEMCO.NS",  "sector":"Cement",   "lot":100,  "weight":1.45},
    {"sym":"GRASIM",     "yf":"GRASIM.NS",      "sector":"Cement",   "lot":475,  "weight":1.12},
    {"sym":"AMBUJACEM",  "yf":"AMBUJACEM.NS",   "sector":"Cement",   "lot":2500, "weight":0.80},
    {"sym":"BHARTIARTL", "yf":"BHARTIARTL.NS",  "sector":"Telecom",  "lot":950,  "weight":5.65},
    {"sym":"TITAN",      "yf":"TITAN.NS",       "sector":"Consumer", "lot":425,  "weight":1.72},
    {"sym":"ASIANPAINT", "yf":"ASIANPAINT.NS",  "sector":"Consumer", "lot":300,  "weight":1.05},
    {"sym":"HAVELLS",    "yf":"HAVELLS.NS",     "sector":"Consumer", "lot":500,  "weight":0.75},
    {"sym":"TRENT",      "yf":"TRENT.NS",       "sector":"Retail",   "lot":275,  "weight":0.70},
    {"sym":"DMART",      "yf":"DMART.NS",       "sector":"Retail",   "lot":350,  "weight":0.80},
    {"sym":"ZOMATO",     "yf":"ZOMATO.NS",      "sector":"Retail",   "lot":3750, "weight":0.65},
    {"sym":"JUBLFOOD",   "yf":"JUBLFOOD.NS",    "sector":"Retail",   "lot":1000, "weight":0.55},
    {"sym":"PIDILITIND", "yf":"PIDILITIND.NS",  "sector":"Chemical", "lot":250,  "weight":0.80},
    {"sym":"SRF",        "yf":"SRF.NS",         "sector":"Chemical", "lot":375,  "weight":0.70},
    {"sym":"DEEPAKNTR",  "yf":"DEEPAKNTR.NS",   "sector":"Chemical", "lot":500,  "weight":0.65},
    {"sym":"BEL",        "yf":"BEL.NS",         "sector":"Defence",  "lot":3500, "weight":0.80},
    {"sym":"HAL",        "yf":"HAL.NS",         "sector":"Defence",  "lot":300,  "weight":0.75},
    {"sym":"BHEL",       "yf":"BHEL.NS",        "sector":"Defence",  "lot":5500, "weight":0.60},
    {"sym":"IRCTC",      "yf":"IRCTC.NS",       "sector":"PSU",      "lot":2500, "weight":0.65},
    {"sym":"IRFC",       "yf":"IRFC.NS",        "sector":"PSU",      "lot":4800, "weight":0.60},
    {"sym":"PFC",        "yf":"PFC.NS",         "sector":"PSU",      "lot":2700, "weight":0.58},
    {"sym":"REC",        "yf":"REC.NS",         "sector":"PSU",      "lot":2700, "weight":0.55},
    {"sym":"RVNL",       "yf":"RVNL.NS",        "sector":"PSU",      "lot":3500, "weight":0.52},
    {"sym":"SIEMENS",    "yf":"SIEMENS.NS",     "sector":"CapGoods", "lot":275,  "weight":0.70},
    {"sym":"ABB",        "yf":"ABB.NS",         "sector":"CapGoods", "lot":175,  "weight":0.65},
    {"sym":"UPL",        "yf":"UPL.NS",         "sector":"Agri",     "lot":2000, "weight":0.60},
    {"sym":"PIIND",      "yf":"PIIND.NS",       "sector":"Agri",     "lot":250,  "weight":0.55},
    {"sym":"COROMANDEL", "yf":"COROMANDEL.NS",  "sector":"Agri",     "lot":500,  "weight":0.52},
    {"sym":"PAYTM",      "yf":"PAYTM.NS",       "sector":"FinTech",  "lot":3750, "weight":0.45},
]


# ═══════════════════════════════════════════════════════
#  DATA FETCH
# ═══════════════════════════════════════════════════════
def fetch_ohlcv(yf_sym: str, days: int = 90) -> pd.DataFrame:
    if not YF_AVAILABLE:
        raise ImportError("yfinance not installed")
    ticker = yf.Ticker(yf_sym)
    df = ticker.history(period=f"{days}d", interval="1d", auto_adjust=True)
    if df.empty or len(df) < 15:
        raise ValueError(f"Insufficient data for {yf_sym}")
    df = df[["Open","High","Low","Close","Volume"]].copy()
    df.columns = ["open","high","low","close","volume"]
    return df.dropna().reset_index(drop=True)


PRICE_MAP = {
    "HDFCBANK":1680,"ICICIBANK":1280,"SBIN":820,"AXISBANK":1180,"KOTAKBANK":1900,
    "BAJFINANCE":6800,"BAJAJFINSV":1680,"TCS":3500,"INFY":1850,"HCLTECH":1650,
    "WIPRO":620,"TECHM":1550,"LTIM":5200,"MPHASIS":2900,"COFORGE":8100,
    "PERSISTENT":5600,"RELIANCE":1310,"ONGC":270,"BPCL":320,"IOC":145,
    "HINDPETRO":330,"GAIL":210,"IGL":380,"NTPC":360,"POWERGRID":320,
    "ADANIGREEN":1800,"ADANIPOWER":560,"TATAPOWER":420,"SUZLON":58,
    "MARUTI":12500,"TATAMOTORS":950,"EICHERMOT":4800,"HEROMOTOCO":4200,
    "BAJAJ-AUTO":9200,"M&M":3100,"TVSMOTORS":2400,"ASHOKLEY":240,
    "SUNPHARMA":1740,"DRREDDY":6200,"CIPLA":1540,"DIVISLAB":5100,
    "AUROPHARMA":1300,"LUPIN":2200,"TORNTPHARM":3300,"ALKEM":5800,
    "APOLLOHOSP":6900,"MAXHEALTH":1100,"FORTIS":680,
    "TATASTEEL":155,"JSWSTEEL":980,"HINDALCO":660,"COALINDIA":455,
    "VEDL":480,"SAIL":120,"NMDC":68,
    "HINDUNILVR":2350,"ITC":465,"NESTLEIND":2320,"TATACONSUM":1050,
    "MARICO":680,"DABUR":550,
    "LT":3650,"ADANIENT":2450,"ADANIPORTS":1380,"GMRINFRA":78,
    "DLF":920,"GODREJPROP":2800,"ULTRACEMCO":11500,"GRASIM":2700,"AMBUJACEM":580,
    "BHARTIARTL":1860,"TITAN":3400,"ASIANPAINT":2250,"HAVELLS":1650,
    "TRENT":6200,"DMART":4100,"ZOMATO":245,"JUBLFOOD":680,
    "PIDILITIND":3200,"SRF":2500,"DEEPAKNTR":2200,
    "BEL":285,"HAL":4200,"BHEL":230,"IRCTC":820,"IRFC":168,
    "PFC":470,"REC":490,"RVNL":410,"SIEMENS":7200,"ABB":7500,
    "UPL":520,"PIIND":3900,"COROMANDEL":1900,"PAYTM":780,
}

def generate_demo_ohlcv(sym: str, days: int = 90) -> pd.DataFrame:
    rng = random.Random(hash(sym) % 99999)
    np_rng = np.random.default_rng(hash(sym) % 99999)
    bp = PRICE_MAP.get(sym, rng.uniform(200, 3000))
    closes = [bp]
    trend = rng.uniform(-0.0015, 0.0025)
    for _ in range(days - 1):
        change = np_rng.normal(trend, 0.014)
        closes.append(max(closes[-1] * (1 + change), bp * 0.3))
    rows = []
    for c in closes:
        spread = c * rng.uniform(0.006, 0.025)
        high = c + spread * rng.uniform(0.4, 1.0)
        low  = c - spread * rng.uniform(0.4, 1.0)
        rows.append({"open": rng.uniform(low, high), "high": high,
                     "low": low, "close": c,
                     "volume": int(rng.uniform(400_000, 10_000_000))})
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════
#  ATR CALCULATOR
# ═══════════════════════════════════════════════════════
def compute_atr(df: pd.DataFrame, period: int = 14) -> float:
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    trs = []
    for i in range(1, len(df)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i]  - closes[i-1]))
        trs.append(tr)
    if not trs:
        return closes[-1] * 0.02
    return float(np.mean(trs[-period:]))


# ═══════════════════════════════════════════════════════
#  RSI CALCULATOR
# ═══════════════════════════════════════════════════════
def compute_rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains  = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = gains[-period:].mean()
    avg_loss = losses[-period:].mean()
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


# ═══════════════════════════════════════════════════════
#  TRADE SETUP ENGINE — Entry · SL · Targets · RR
# ═══════════════════════════════════════════════════════
def compute_trade_setup(df: pd.DataFrame, smc: dict) -> dict:
    """
    Compute precise entry, stop-loss, targets T1/T2/T3,
    risk-reward ratios, and entry timing condition.
    """
    if smc is None or df is None or len(df) < 20:
        return None

    closes = df["close"].values
    highs  = df["high"].values
    lows   = df["low"].values
    last   = closes[-1]
    score  = smc["smcScore"]

    atr = compute_atr(df, 14)
    rsi = compute_rsi(closes, 14)

    # Direction
    if score >= 15:
        direction = "LONG"
    elif score <= -15:
        direction = "SHORT"
    else:
        return None  # No trade — neutral zone

    # ── ENTRY ZONE ──
    # ATR-based entry: enter on pullback to entry zone
    if direction == "LONG":
        entry_ideal  = round(last, 2)
        entry_low    = round(last - atr * 0.3, 2)   # limit order lower bound
        entry_high   = round(last + atr * 0.15, 2)  # max chase price
        # Stop Loss: below recent swing low or 1.5x ATR
        recent_low   = lows[-10:].min()
        sl           = round(min(recent_low - atr * 0.2, last - atr * 1.5), 2)
        # Targets
        risk         = entry_ideal - sl
        t1           = round(entry_ideal + risk * 1.5, 2)   # T1: 1:1.5
        t2           = round(entry_ideal + risk * 2.5, 2)   # T2: 1:2.5
        t3           = round(entry_ideal + risk * 4.0, 2)   # T3: 1:4 (multibagger zone)
    else:  # SHORT
        entry_ideal  = round(last, 2)
        entry_low    = round(last - atr * 0.15, 2)
        entry_high   = round(last + atr * 0.3, 2)
        recent_high  = highs[-10:].max()
        sl           = round(max(recent_high + atr * 0.2, last + atr * 1.5), 2)
        risk         = sl - entry_ideal
        t1           = round(entry_ideal - risk * 1.5, 2)
        t2           = round(entry_ideal - risk * 2.5, 2)
        t3           = round(entry_ideal - risk * 4.0, 2)

    risk_per_share = abs(entry_ideal - sl)
    rr1 = round(abs(t1 - entry_ideal) / risk_per_share, 2) if risk_per_share > 0 else 0
    rr2 = round(abs(t2 - entry_ideal) / risk_per_share, 2) if risk_per_share > 0 else 0
    rr3 = round(abs(t3 - entry_ideal) / risk_per_share, 2) if risk_per_share > 0 else 0

    sl_pct   = round(abs(entry_ideal - sl) / entry_ideal * 100, 2)
    t1_pct   = round(abs(t1 - entry_ideal) / entry_ideal * 100, 2)
    t2_pct   = round(abs(t2 - entry_ideal) / entry_ideal * 100, 2)
    t3_pct   = round(abs(t3 - entry_ideal) / entry_ideal * 100, 2)

    # ── ENTRY TIMING ──
    timing_conditions = []
    entry_trigger     = "WAIT"

    if direction == "LONG":
        if last <= entry_high and last >= entry_low:
            entry_trigger = "ENTER NOW"
        elif last < entry_low:
            entry_trigger = "ENTER NOW (dipped into zone)"
        else:
            entry_trigger = f"WAIT — enter on pullback to ₹{entry_low:.0f}–{entry_high:.0f}"
        if rsi < 40:
            timing_conditions.append(f"RSI {rsi} oversold — good entry")
        elif rsi > 70:
            timing_conditions.append(f"RSI {rsi} overbought — wait for pullback")
        else:
            timing_conditions.append(f"RSI {rsi} — neutral momentum")
        if any("BOS↑" in p for p in smc["patterns"]):
            timing_conditions.append("BOS confirmed — structure bullish")
        if any("LiqGrab↑" in p for p in smc["patterns"]):
            timing_conditions.append("Liquidity grab — reversal likely")
        if any("OB" in p and "Bull" in p for p in smc["patterns"]):
            timing_conditions.append("Order block zone active — institutional demand")
    else:  # SHORT
        if last >= entry_low and last <= entry_high:
            entry_trigger = "ENTER NOW"
        elif last > entry_high:
            entry_trigger = "ENTER NOW (spiked into zone)"
        else:
            entry_trigger = f"WAIT — enter on rally to ₹{entry_low:.0f}–{entry_high:.0f}"
        if rsi > 65:
            timing_conditions.append(f"RSI {rsi} overbought — good short entry")
        elif rsi < 35:
            timing_conditions.append(f"RSI {rsi} oversold — wait before shorting")
        else:
            timing_conditions.append(f"RSI {rsi} — neutral, monitor")
        if any("BOS↓" in p for p in smc["patterns"]):
            timing_conditions.append("BOS confirmed — structure bearish")
        if any("LiqGrab↓" in p for p in smc["patterns"]):
            timing_conditions.append("Sell-side liquidity grab — reversal likely")

    return {
        "direction":    direction,
        "entry_ideal":  entry_ideal,
        "entry_low":    entry_low,
        "entry_high":   entry_high,
        "entry_trigger":entry_trigger,
        "sl":           sl,
        "sl_pct":       sl_pct,
        "t1":           t1, "t1_pct": t1_pct, "rr1": rr1,
        "t2":           t2, "t2_pct": t2_pct, "rr2": rr2,
        "t3":           t3, "t3_pct": t3_pct, "rr3": rr3,
        "atr":          round(atr, 2),
        "rsi":          rsi,
        "risk_per_share": round(risk_per_share, 2),
        "timing_conditions": timing_conditions,
    }


# ═══════════════════════════════════════════════════════
#  MULTIBAGGER DETECTOR
# ═══════════════════════════════════════════════════════
def detect_multibagger(df: pd.DataFrame, smc: dict, stock: dict) -> dict:
    """
    Detect multibagger potential: RSI divergence + volume surge +
    breakout + discount zone + strong SMC confluence.
    Returns dict with is_multibagger, score, and reasons.
    """
    if smc is None or df is None or len(df) < 30:
        return {"is_multibagger": False, "mb_score": 0, "mb_reasons": []}

    closes = df["close"].values
    highs  = df["high"].values
    lows   = df["low"].values
    vols   = df["volume"].values

    mb_score   = 0
    mb_reasons = []

    # 1. RSI Divergence: price lower low but RSI higher low
    rsi_now  = compute_rsi(closes, 14)
    rsi_prev = compute_rsi(closes[:-5], 14)
    price_ll = closes[-1] < closes[-10]
    rsi_hl   = rsi_now > rsi_prev
    if price_ll and rsi_hl:
        mb_score += 25
        mb_reasons.append(f"RSI divergence — price lower but RSI rising ({rsi_prev:.0f}→{rsi_now:.0f})")

    # 2. Volume surge (2x+ average)
    avg_vol20 = vols[-20:].mean()
    vol_ratio = vols[-1] / avg_vol20 if avg_vol20 > 0 else 1
    if vol_ratio >= 2.0:
        mb_score += 20
        mb_reasons.append(f"Volume surge {vol_ratio:.1f}x avg — institutional accumulation")

    # 3. In discount zone (below 50% of 52-week range)
    high52 = highs[-min(252, len(highs)):].max()
    low52  = lows[-min(252, len(lows)):].min()
    pos_in_range = (closes[-1] - low52) / max(high52 - low52, 1) * 100
    if pos_in_range < 35:
        mb_score += 20
        mb_reasons.append(f"Deep discount: {pos_in_range:.0f}% from 52-week range (near lows)")
    elif pos_in_range < 50:
        mb_score += 10
        mb_reasons.append(f"Discount zone: {pos_in_range:.0f}% of 52-week range")

    # 4. Strong SMC score
    if smc["smcScore"] >= 50:
        mb_score += 20
        mb_reasons.append(f"Strong SMC confluence score: +{smc['smcScore']}")
    elif smc["smcScore"] >= 30:
        mb_score += 10
        mb_reasons.append(f"Good SMC score: +{smc['smcScore']}")

    # 5. Multiple bullish patterns
    bull_pats = [p for p in smc["patterns"] if "↑" in p or "Bull" in p or "Discount" in p]
    if len(bull_pats) >= 3:
        mb_score += 15
        mb_reasons.append(f"{len(bull_pats)} bullish patterns aligned: {', '.join(bull_pats[:3])}")

    # 6. Potential upside to 52-week high (30%+ potential)
    upside_pct = (high52 - closes[-1]) / closes[-1] * 100
    if upside_pct >= 40:
        mb_score += 10
        mb_reasons.append(f"₹{upside_pct:.0f}% upside to 52-week high ₹{high52:.0f}")

    is_multibagger = mb_score >= 55

    return {
        "is_multibagger": is_multibagger,
        "mb_score":       mb_score,
        "mb_reasons":     mb_reasons,
        "pos_in_range":   round(pos_in_range, 1),
        "upside_to_high": round(upside_pct, 1),
        "rsi":            rsi_now,
    }


# ═══════════════════════════════════════════════════════
#  SMC ENGINE (unchanged from original)
# ═══════════════════════════════════════════════════════
def compute_smc(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 15:
        return None
    n      = len(df)
    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    vols   = df["volume"].values
    signals   = []
    smc_score = 0

    def swing_highs(period=4):
        out = []
        for i in range(period, n - period):
            w = highs[i - period: i + period + 1]
            if highs[i] == w.max():
                out.append({"idx": i, "price": float(highs[i])})
        return out

    def swing_lows(period=4):
        out = []
        for i in range(period, n - period):
            w = lows[i - period: i + period + 1]
            if lows[i] == w.min():
                out.append({"idx": i, "price": float(lows[i])})
        return out

    s_highs = swing_highs()
    s_lows  = swing_lows()

    if s_highs and closes[-1] > s_highs[-1]["price"]:
        signals.append({"type":"BOS","dir":"BULL","label":"BOS↑",
            "desc":f"Bullish BOS above swing high ₹{s_highs[-1]['price']:.2f}"})
        smc_score += 30
    if s_lows and closes[-1] < s_lows[-1]["price"]:
        signals.append({"type":"BOS","dir":"BEAR","label":"BOS↓",
            "desc":f"Bearish BOS below swing low ₹{s_lows[-1]['price']:.2f}"})
        smc_score -= 30
    if len(s_highs) >= 2 and len(s_lows) >= 2:
        h1,h2 = s_highs[-2]["price"], s_highs[-1]["price"]
        l1,l2 = s_lows[-2]["price"],  s_lows[-1]["price"]
        if h2 > h1 and l2 > l1 and closes[-1] < l2:
            signals.append({"type":"CHoCH","dir":"BEAR","label":"CHoCH↓",
                "desc":f"Uptrend broken — CHoCH at ₹{closes[-1]:.2f}"})
            smc_score -= 22
        if h2 < h1 and l2 < l1 and closes[-1] > h2:
            signals.append({"type":"CHoCH","dir":"BULL","label":"CHoCH↑",
                "desc":f"Downtrend broken — CHoCH at ₹{closes[-1]:.2f}"})
            smc_score += 22

    for i in range(max(0, n-15), n-3):
        co,cc,cl,ch = opens[i],closes[i],lows[i],highs[i]
        if cc < co:
            rally = [(opens[j],closes[j]) for j in range(i+1, min(i+4,n))]
            if len(rally)==3 and all(c>o for o,c in rally):
                if (rally[-1][1]-cc)/cc > 0.012 and lows[-1]<=ch and highs[-1]>=cl:
                    signals.append({"type":"OB","dir":"BULL","label":"Bull OB 📦",
                        "desc":f"Bullish OB ₹{cl:.2f}–₹{ch:.2f} retesting"})
                    smc_score += 28; break
        if cc > co:
            drop = [(opens[j],closes[j]) for j in range(i+1, min(i+4,n))]
            if len(drop)==3 and all(c<o for o,c in drop):
                if (cc-drop[-1][1])/cc > 0.012 and lows[-1]<=ch and highs[-1]>=cl:
                    signals.append({"type":"OB","dir":"BEAR","label":"Bear OB 📦",
                        "desc":f"Bearish OB ₹{cl:.2f}–₹{ch:.2f} supply"})
                    smc_score -= 25; break

    for i in range(max(0, n-20), n-2):
        c1h,c1l = highs[i],lows[i]
        c3l,c3h = lows[i+2],highs[i+2]
        if c3l > c1h and (c3l-c1h)/c1h > 0.003:
            ig = c1h < closes[-1] < c3l
            signals.append({"type":"FVG","dir":"BULL","label":"FVG↑ 🕳️",
                "desc":f"Bullish FVG ₹{c1h:.2f}–₹{c3l:.2f}{' (in gap)' if ig else ''}"})
            smc_score += 18 if ig else 10; break
        if c3h < c1l and (c1l-c3h)/c1l > 0.003:
            ig = c3h < closes[-1] < c1l
            signals.append({"type":"FVG","dir":"BEAR","label":"FVG↓ 🕳️",
                "desc":f"Bearish FVG ₹{c3h:.2f}–₹{c1l:.2f}{' (in gap)' if ig else ''}"})
            smc_score -= 15 if ig else 8; break

    r20h = highs[-20:-1].max() if n>=20 else highs[:-1].max()
    r20l = lows[-20:-1].min()  if n>=20 else lows[:-1].min()
    mid  = (lows[-1]+highs[-1])/2
    if lows[-1] < r20l and closes[-1] > mid:
        signals.append({"type":"LIQ","dir":"BULL","label":"LiqGrab↑ 💧",
            "desc":f"Buy-side stop hunt below ₹{r20l:.2f}"})
        smc_score += 25
    if highs[-1] > r20h and closes[-1] < mid:
        signals.append({"type":"LIQ","dir":"BEAR","label":"LiqGrab↓ 💧",
            "desc":f"Sell-side stop hunt above ₹{r20h:.2f}"})
        smc_score -= 22

    avg_vol  = vols[-20:].mean() if n>=20 else vols.mean()
    vol_ratio= vols[-1] / avg_vol if avg_vol > 0 else 1.0
    if vol_ratio > 1.8:
        if closes[-1] > opens[-1]:
            signals.append({"type":"VOL","dir":"BULL","label":f"Vol {vol_ratio:.1f}x 📊",
                "desc":f"Institutional buying {vol_ratio:.1f}x avg"})
            smc_score += 15
        else:
            signals.append({"type":"VOL","dir":"BEAR","label":f"Vol {vol_ratio:.1f}x 📊",
                "desc":f"Institutional selling {vol_ratio:.1f}x avg"})
            smc_score -= 12

    rh = highs[-20:].max() if n>=20 else highs.max()
    rl = lows[-20:].min()  if n>=20 else lows.min()
    eq = (rh+rl)/2
    if closes[-1] < eq*0.995 and smc_score > 0:
        signals.append({"type":"ZONE","dir":"BULL","label":"Discount🟢",
            "desc":f"Discount {((eq-closes[-1])/eq*100):.1f}% below EQ ₹{eq:.2f}"})
        smc_score += 10
    if closes[-1] > eq*1.005 and smc_score < 0:
        signals.append({"type":"ZONE","dir":"BEAR","label":"Premium🔴",
            "desc":f"Premium {((closes[-1]-eq)/eq*100):.1f}% above EQ"})
        smc_score -= 8

    bull_sigs = sum(1 for s in signals if s["dir"]=="BULL")
    bear_sigs = sum(1 for s in signals if s["dir"]=="BEAR")
    if abs(bull_sigs-bear_sigs) >= 2:
        smc_score += 10 if bull_sigs > bear_sigs else -10
    smc_score = max(-100, min(100, round(smc_score)))

    pct_change = ((closes[-1]-closes[-2])/closes[-2]*100) if len(closes)>1 else 0
    return {
        "patterns":    [s["label"] for s in signals],
        "signals":     signals,
        "smcScore":    smc_score,
        "lastClose":   round(float(closes[-1]),2),
        "prevClose":   round(float(closes[-2]),2) if len(closes)>1 else 0,
        "pctChange":   round(float(pct_change),2),
        "high":        round(float(highs[-1]),2),
        "low":         round(float(lows[-1]),2),
        "open":        round(float(opens[-1]),2),
        "volume":      int(vols[-1]),
        "avgVol":      int(avg_vol),
        "volRatio":    round(float(vol_ratio),1),
        "dayRange":    round(float((highs[-1]-lows[-1])/lows[-1]*100),2),
        "bullSignals": bull_sigs,
        "bearSignals": bear_sigs,
        "equilibrium": round(float(eq),2),
        "rangeHigh":   round(float(rh),2),
        "rangeLow":    round(float(rl),2),
    }


# ═══════════════════════════════════════════════════════
#  SCAN RUNNER
# ═══════════════════════════════════════════════════════
import time

def run_scan(stocks: list, demo: bool = False, verbose: bool = True) -> list:
    results = []
    total   = len(stocks)
    for idx, stock in enumerate(stocks):
        sym = stock["sym"]
        pct = int((idx+1)/total*100)
        bar = "█"*(pct//5) + "░"*(20-pct//5)
        if verbose:
            print(f"\r  [{bar}] {pct:3d}%  {sym:<14}", end="", flush=True)
        try:
            df  = generate_demo_ohlcv(sym) if demo else fetch_ohlcv(stock["yf"])
            smc = compute_smc(df)
            ts  = compute_trade_setup(df, smc)
            mb  = detect_multibagger(df, smc, stock)
            result = {**stock, "smc": smc, "smcScore": smc["smcScore"] if smc else 0,
                      "trade_setup": ts, "multibagger": mb, "error": None}
            if verbose and smc:
                mb_flag = " 💎MULTIBAGGER" if mb.get("is_multibagger") else ""
                print(f"\r  ✓ {sym:<14} Score:{smc['smcScore']:+4d}  "
                      f"{'LONG' if ts and ts['direction']=='LONG' else 'SHORT' if ts else '----'}  "
                      f"₹{smc['lastClose']:<10.2f}{mb_flag}", flush=True)
        except Exception as e:
            result = {**stock, "smc":None,"smcScore":-999,
                      "trade_setup":None,"multibagger":None,"error":str(e)}
            if verbose:
                print(f"\r  ✗ {sym:<14} {str(e)[:50]}", flush=True)
        results.append(result)
        if not demo:
            time.sleep(0.12)
    if verbose:
        print()
    return results


# ═══════════════════════════════════════════════════════
#  WEEKLY PICKS GENERATOR
# ═══════════════════════════════════════════════════════
def generate_weekly_picks(results: list) -> dict:
    """Pick top 3 LONG, top 2 SHORT, and top 3 Multibaggers for the week."""
    valid = [r for r in results if r["smc"] and r["smcScore"] != -999]

    # Top LONG picks: score >= 20, has trade setup, sorted by score + mb_score
    longs = sorted(
        [r for r in valid if r["smcScore"] >= 20 and r.get("trade_setup")],
        key=lambda r: r["smcScore"] + r["multibagger"]["mb_score"] * 0.5,
        reverse=True
    )[:3]

    # Top SHORT picks
    shorts = sorted(
        [r for r in valid if r["smcScore"] <= -20 and r.get("trade_setup")],
        key=lambda r: r["smcScore"],
    )[:2]

    # Multibaggers
    mbs = sorted(
        [r for r in valid if r.get("multibagger", {}).get("is_multibagger")],
        key=lambda r: r["multibagger"]["mb_score"],
        reverse=True
    )[:3]

    return {"longs": longs, "shorts": shorts, "multibaggers": mbs}


# ═══════════════════════════════════════════════════════
#  HTML BUILDER — Full Dashboard
# ═══════════════════════════════════════════════════════
def sentiment_label(score):
    if score >= 50:  return "STRONG BULL", "#00e5a0"
    if score >= 20:  return "BULLISH",     "#4ade80"
    if score >= -10: return "NEUTRAL",     "#f5c842"
    if score >= -40: return "BEARISH",     "#f97316"
    return "STRONG BEAR", "#f56060"

def sig_icon(t):
    return {"BOS":"⚡","CHoCH":"🔄","OB":"📦","FVG":"🕳️","LIQ":"💧","VOL":"📊","ZONE":"⚖️"}.get(t,"●")

def chip_cls(label):
    if any(x in label for x in ["↑","Bull","Discount","LiqGrab↑"]): return "cb"
    if any(x in label for x in ["↓","Bear","Premium","LiqGrab↓"]):  return "cr"
    return "cn"


def build_weekly_picks_html(picks: dict) -> str:
    def pick_card(r, label_color, rank_icon):
        smc = r["smc"]
        ts  = r.get("trade_setup") or {}
        mb  = r.get("multibagger") or {}
        sc_c = "#00e5a0" if r["smcScore"] >= 0 else "#f56060"
        d    = ts.get("direction","—")
        dir_c = "#00e5a0" if d=="LONG" else "#f56060"
        return f"""
        <div class="pick-card">
          <div class="pick-header">
            <span class="pick-rank">{rank_icon}</span>
            <div>
              <div class="pick-sym">{r['sym']}</div>
              <div class="pick-sector">{r['sector']} · Lot {r['lot']}</div>
            </div>
            <div class="pick-score" style="color:{sc_c}">{r['smcScore']:+d}</div>
            <div class="pick-dir" style="background:{'rgba(0,229,160,.15)' if d=='LONG' else 'rgba(245,96,96,.15)' if d=='SHORT' else 'rgba(245,200,66,.1)'};color:{dir_c}">{d}</div>
          </div>
          <div class="pick-price-row">
            <span class="pick-cmp">CMP ₹{smc['lastClose']}</span>
            <span class="pick-chg" style="color:{'#00e5a0' if smc['pctChange']>=0 else '#f56060'}">{smc['pctChange']:+.2f}%</span>
          </div>
          <div class="pick-levels">
            <div class="level-row"><span class="level-lbl">ENTRY</span>
              <span class="level-val entry">₹{ts.get('entry_low','—')} – ₹{ts.get('entry_high','—')}</span>
              <span class="level-trigger">{ts.get('entry_trigger','—')}</span>
            </div>
            <div class="level-row"><span class="level-lbl">STOP LOSS</span>
              <span class="level-val sl">₹{ts.get('sl','—')} <span class="level-pct">(-{ts.get('sl_pct','—')}%)</span></span>
            </div>
            <div class="level-row"><span class="level-lbl">TARGET 1</span>
              <span class="level-val t1">₹{ts.get('t1','—')} <span class="level-pct">(+{ts.get('t1_pct','—')}% · RR {ts.get('rr1','—')})</span></span>
            </div>
            <div class="level-row"><span class="level-lbl">TARGET 2</span>
              <span class="level-val t2">₹{ts.get('t2','—')} <span class="level-pct">(+{ts.get('t2_pct','—')}% · RR {ts.get('rr2','—')})</span></span>
            </div>
            <div class="level-row"><span class="level-lbl">TARGET 3</span>
              <span class="level-val t3">₹{ts.get('t3','—')} <span class="level-pct">(+{ts.get('t3_pct','—')}% · RR {ts.get('rr3','—')})</span></span>
            </div>
          </div>
          {''.join(f'<div class="timing-row">✓ {c}</div>' for c in ts.get('timing_conditions',[]))}
          {f'<div class="mb-badge">💎 MULTIBAGGER · MB Score {mb.get("mb_score",0)} · Upside {mb.get("upside_to_high",0):.0f}%</div>' if mb.get('is_multibagger') else ''}
          <div class="pick-patterns">{''.join(f'<span class="chip {chip_cls(p)}">{p}</span>' for p in smc["patterns"][:4])}</div>
        </div>"""

    longs_html = "".join(pick_card(r,"#00e5a0",["🥇","🥈","🥉"][i]) for i,r in enumerate(picks["longs"]))
    shorts_html = "".join(pick_card(r,"#f56060",["🔻","🔻🔻"][i] if i<2 else "↓") for i,r in enumerate(picks["shorts"]))
    mbs_html   = "".join(pick_card(r,"#f5c842",["💎","💎💎","💎💎💎"][i]) for i,r in enumerate(picks["multibaggers"]))

    no_longs  = '<div class="no-picks">No high-confidence long setups this week</div>' if not picks["longs"] else ""
    no_shorts = '<div class="no-picks">No high-confidence short setups this week</div>' if not picks["shorts"] else ""
    no_mbs    = '<div class="no-picks">No multibagger setups detected this week</div>' if not picks["multibaggers"] else ""

    return f"""
    <section class="weekly-section">
      <div class="weekly-header">
        <h2>📅 THIS WEEK'S BEST TRADES</h2>
        <div class="weekly-sub">High-confidence setups with precise Entry · SL · Targets · RR</div>
      </div>
      <div class="weekly-grid">
        <div class="weekly-col">
          <div class="wcol-header bull">🟢 TOP LONG SETUPS</div>
          {longs_html or no_longs}
        </div>
        <div class="weekly-col">
          <div class="wcol-header bear">🔴 TOP SHORT SETUPS</div>
          {shorts_html or no_shorts}
        </div>
        <div class="weekly-col">
          <div class="wcol-header mb">💎 MULTIBAGGER CANDIDATES</div>
          {mbs_html or no_mbs}
        </div>
      </div>
    </section>"""


def build_result_rows_html(sorted_results: list) -> str:
    rows_html = ""
    for i, r in enumerate(sorted_results):
        rank = i + 1
        smc  = r["smc"]
        ts   = r.get("trade_setup") or {}
        mb   = r.get("multibagger") or {}
        sent_label, sent_color = sentiment_label(r["smcScore"])
        up   = smc["pctChange"] >= 0
        chg_c= "#00e5a0" if up else "#f56060"
        sc_c = "#00e5a0" if r["smcScore"] >= 0 else "#f56060"
        rank_icon = ["🥇","🥈","🥉"][rank-1] if rank <= 3 else f"#{rank}"

        chips_html = "".join(
            f'<span class="chip {chip_cls(p)}">{p}</span>'
            for p in smc["patterns"][:4]
        ) if smc["patterns"] else '<span class="chip cn">NO SIGNAL</span>'

        mb_badge = '<span class="mb-inline">💎 MB</span>' if mb.get("is_multibagger") else ""

        # Signal detail rows
        sig_rows = "".join(
            f'<div class="sig-row"><span>{sig_icon(s["type"])}</span>'
            f'<span style="color:{"#00e5a0" if s["dir"]=="BULL" else "#f56060" if s["dir"]=="BEAR" else "#f5c842"}">'
            f'{s["desc"]}</span></div>'
            for s in smc["signals"]
        ) or '<div style="color:#304560;font-size:11px">No SMC confluence detected</div>'

        # Trade setup table
        if ts:
            d = ts["direction"]
            dir_c = "#00e5a0" if d == "LONG" else "#f56060"
            trade_html = f"""
            <div class="trade-setup-box">
              <div class="ts-header">
                <span style="color:{dir_c};font-weight:700">{d}</span>
                <span class="ts-trigger">{ts['entry_trigger']}</span>
                <span style="color:#304560;font-size:10px">ATR: ₹{ts['atr']} · RSI: {ts['rsi']}</span>
              </div>
              <div class="ts-levels">
                <div class="ts-row"><span class="tsl entry-l">ENTRY ZONE</span><span class="tsv">₹{ts['entry_low']} – ₹{ts['entry_high']}</span></div>
                <div class="ts-row"><span class="tsl sl-l">STOP LOSS</span><span class="tsv sl-v">₹{ts['sl']} <small>(-{ts['sl_pct']}%)</small></span></div>
                <div class="ts-row"><span class="tsl t1-l">TARGET 1</span><span class="tsv t1-v">₹{ts['t1']} <small>(+{ts['t1_pct']}% · RR {ts['rr1']})</small></span></div>
                <div class="ts-row"><span class="tsl t2-l">TARGET 2</span><span class="tsv t2-v">₹{ts['t2']} <small>(+{ts['t2_pct']}% · RR {ts['rr2']})</small></span></div>
                <div class="ts-row"><span class="tsl t3-l">TARGET 3</span><span class="tsv t3-v">₹{ts['t3']} <small>(+{ts['t3_pct']}% · RR {ts['rr3']})</small></span></div>
              </div>
              {''.join(f'<div class="timing-row">✓ {c}</div>' for c in ts.get('timing_conditions',[]))}
            </div>"""
        else:
            trade_html = '<div style="font-family:monospace;font-size:10px;color:#304560;padding:8px">Neutral — no trade setup</div>'

        mb_detail = ""
        if mb.get("is_multibagger"):
            mb_detail = f"""
            <div class="mb-detail-box">
              <div class="mb-detail-header">💎 MULTIBAGGER SETUP · Score {mb['mb_score']}/100</div>
              {''.join(f'<div class="mb-reason">• {r}</div>' for r in mb['mb_reasons'])}
              <div class="mb-stats">
                <span>Position in range: {mb['pos_in_range']}%</span>
                <span>Upside to 52W High: {mb['upside_to_high']}%</span>
                <span>RSI: {mb['rsi']}</span>
              </div>
            </div>"""

        # Mini stats
        mini = "".join(
            f'<div class="ms-card"><div class="ms-lbl">{l}</div><div class="ms-val" style="color:{c}">{v}</div></div>'
            for l, v, c in [
                ("SMC Score",   f'{r["smcScore"]:+d}',         sc_c),
                ("Equilibrium", f'₹{smc["equilibrium"]}',      "#2d7ff9"),
                ("Day High",    f'₹{smc["high"]}',             "#00e5a0"),
                ("Day Low",     f'₹{smc["low"]}',              "#f56060"),
                ("Vol Ratio",   f'{smc["volRatio"]}x',         "#f5c842" if float(smc["volRatio"])>=1.8 else "#304560"),
                ("Day Range",   f'{smc["dayRange"]}%',         "#9d7cfc"),
                ("Bull Sigs",   smc["bullSignals"],             "#00e5a0"),
                ("Bear Sigs",   smc["bearSignals"],             "#f56060"),
            ]
        )

        rows_html += f"""
        <div class="result-row" data-score="{r['smcScore']}" data-sector="{r['sector']}"
             data-sent="{'BULL' if r['smcScore']>=20 else 'BEAR' if r['smcScore']<=-20 else 'NEUTRAL'}"
             data-mb="{'1' if mb.get('is_multibagger') else '0'}">
          <div class="row-main" onclick="toggleRow('{r['sym']}_{i}')">
            <div class="rank">{rank_icon}</div>
            <div>
              <div class="sym">{r['sym']}{mb_badge}</div>
              <div class="sec-tag">{r['sector']} · {r['lot']}</div>
            </div>
            <div class="score" style="color:{sc_c}">{r['smcScore']:+d}</div>
            <div class="col-chips">{chips_html}</div>
            <div class="col-price">
              <div class="price">₹{smc['lastClose']}</div>
              <div class="pct-chg" style="color:{chg_c}">{'+' if up else ''}{smc['pctChange']}%</div>
            </div>
            <div class="sent-badge" style="background:{sent_color}18;color:{sent_color};border:1px solid {sent_color}30">{sent_label}</div>
            <div class="vol-c" style="color:{'#f5c842' if float(smc['volRatio'])>=1.8 else '#304560'}">{smc['volRatio']}x</div>
            <div class="ts-preview" style="color:{'#00e5a0' if ts.get('direction')=='LONG' else '#f56060' if ts.get('direction')=='SHORT' else '#304560'}">
              {ts.get('direction','—')} {f'SL ₹{ts["sl"]}' if ts else ''}
            </div>
            <div class="expand-icon" id="icon-{r['sym']}_{i}">▼</div>
          </div>
          <div class="row-detail" id="detail-{r['sym']}_{i}" style="display:none">
            <div class="detail-3col">
              <div>
                <div class="detail-title">SMC Signals ({len(smc['signals'])})</div>
                <div class="sig-list">{sig_rows}</div>
                <div class="mini-stats">{mini}</div>
              </div>
              <div>{trade_html}</div>
              <div>{mb_detail}</div>
            </div>
          </div>
        </div>"""
    return rows_html


def build_html(results: list, scan_meta: dict) -> str:
    valid     = [r for r in results if r["smc"] and r["smcScore"] != -999]
    errors    = [r for r in results if r.get("error")]
    bull      = sum(1 for r in valid if r["smcScore"] >= 20)
    bear      = sum(1 for r in valid if r["smcScore"] <= -20)
    strong    = sum(1 for r in valid if r["smcScore"] >= 50)
    mbs_count = sum(1 for r in valid if r.get("multibagger",{}).get("is_multibagger"))
    avg_sc    = round(sum(r["smcScore"] for r in valid) / len(valid)) if valid else 0
    sorted_r  = sorted(valid, key=lambda r: r["smcScore"], reverse=True)
    sectors   = sorted(set(r["sector"] for r in valid))
    scan_time = scan_meta.get("scan_time", datetime.now().strftime("%d %b %Y, %I:%M %p"))
    mode_str  = "DEMO" if scan_meta.get("demo") else "LIVE YAHOO FINANCE"
    picks     = generate_weekly_picks(results)

    weekly_html  = build_weekly_picks_html(picks)
    rows_html    = build_result_rows_html(sorted_r)
    sector_btns  = "".join(f'<button class="fb" onclick="filterSector(this,\'{s}\')">{s}</button>' for s in sectors)
    sector_bars  = "".join(
        f'<div class="sec-bar"><div class="sb-lbl"><span>{s}</span>'
        f'<span style="color:{"#00e5a0" if avg_s>=0 else "#f56060"}">{avg_s:+d}</span></div>'
        f'<div class="sb-track"><div class="sb-fill" style="width:{min(100,max(0,(avg_s+100)/2))}%;'
        f'background:{"#00e5a0" if avg_s>=0 else "#f56060"}"></div></div></div>'
        for s in sectors
        for sec_stocks in [[r for r in valid if r["sector"]==s]]
        for avg_s in [round(sum(r["smcScore"] for r in sec_stocks)/len(sec_stocks)) if sec_stocks else 0]
    )
    err_html = (f'<div class="err-note">⚠ {len(errors)} errors: '
                f'{", ".join(r["sym"] for r in errors[:8])}...</div>') if errors else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NSE F&O SMC Scanner — {scan_time}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --bg:#04060c;--s1:#080c18;--s2:#0b1020;--b1:#131d2e;--b2:#1a2840;
  --tx:#c8daf5;--mu:#304560;--dm:#1a2535;
  --g:#00e5a0;--b:#2d7ff9;--y:#f5c842;--r:#f56060;--o:#f97316;--p:#9d7cfc;
  --mono:'JetBrains Mono',monospace;--dis:'Orbitron',monospace;--body:'Rajdhani',sans-serif;
}}
body{{background:var(--bg);font-family:var(--body);color:var(--tx);min-height:100vh;}}
body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,229,160,.005) 3px,rgba(0,229,160,.005) 4px);}}
.wrap{{max-width:1300px;margin:0 auto;padding:14px 12px 60px;position:relative;z-index:1;}}

/* HEADER */
.hdr{{text-align:center;padding:22px 0 16px;border-bottom:1px solid var(--b1);margin-bottom:16px;
  background:radial-gradient(ellipse 70% 100% at 50% 0%,rgba(45,127,249,.05) 0%,transparent 70%);}}
.badge{{font-family:var(--mono);font-size:9px;letter-spacing:.2em;color:var(--g);
  border:1px solid rgba(0,229,160,.2);padding:3px 10px;border-radius:20px;
  display:inline-flex;align-items:center;gap:5px;margin-bottom:8px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--g);}}
h1{{font-family:var(--dis);font-size:clamp(15px,3.5vw,30px);font-weight:900;letter-spacing:.1em;
  background:linear-gradient(90deg,#fff 0%,#2d7ff9 35%,#00e5a0 70%,#9d7cfc 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.hdr-sub{{font-family:var(--mono);font-size:9px;color:var(--mu);letter-spacing:.08em;margin-top:5px;}}
.scan-meta{{display:flex;justify-content:center;gap:16px;margin-top:10px;flex-wrap:wrap;}}
.meta-item{{font-family:var(--mono);font-size:9px;color:var(--mu);
  padding:3px 10px;border:1px solid var(--b2);border-radius:4px;}}
.meta-item span{{color:var(--g);font-weight:600;}}

/* STATS */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:7px;margin-bottom:14px;}}
.stat{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;padding:9px 11px;text-align:center;}}
.stat-lbl{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.14em;margin-bottom:3px;}}
.stat-val{{font-family:var(--dis);font-size:20px;font-weight:700;}}

/* ═══ WEEKLY PICKS ═══ */
.weekly-section{{margin-bottom:20px;}}
.weekly-header{{text-align:center;margin-bottom:14px;}}
.weekly-header h2{{font-family:var(--dis);font-size:clamp(14px,2.5vw,22px);letter-spacing:.12em;
  background:linear-gradient(90deg,#f5c842,#00e5a0);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text;}}
.weekly-sub{{font-family:var(--mono);font-size:9px;color:var(--mu);letter-spacing:.08em;margin-top:4px;}}
.weekly-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;}}
.weekly-col{{display:flex;flex-direction:column;gap:8px;}}
.wcol-header{{font-family:var(--dis);font-size:11px;letter-spacing:.1em;padding:8px 14px;
  border-radius:7px;text-align:center;margin-bottom:4px;}}
.wcol-header.bull{{background:rgba(0,229,160,.1);color:var(--g);border:1px solid rgba(0,229,160,.2);}}
.wcol-header.bear{{background:rgba(245,96,96,.1);color:var(--r);border:1px solid rgba(245,96,96,.2);}}
.wcol-header.mb{{background:rgba(245,200,66,.1);color:var(--y);border:1px solid rgba(245,200,66,.2);}}

.pick-card{{background:var(--s1);border:1px solid var(--b2);border-radius:10px;padding:14px;}}
.pick-header{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}
.pick-rank{{font-size:20px;}}
.pick-sym{{font-family:var(--dis);font-size:16px;font-weight:900;color:#fff;letter-spacing:.05em;}}
.pick-sector{{font-family:var(--mono);font-size:8px;color:var(--mu);margin-top:2px;}}
.pick-score{{font-family:var(--dis);font-size:20px;font-weight:900;margin-left:auto;}}
.pick-dir{{font-family:var(--dis);font-size:10px;font-weight:700;padding:4px 10px;border-radius:5px;letter-spacing:.08em;}}
.pick-price-row{{display:flex;gap:10px;align-items:center;margin-bottom:10px;}}
.pick-cmp{{font-family:var(--mono);font-size:14px;font-weight:700;color:var(--tx);}}
.pick-chg{{font-family:var(--mono);font-size:11px;}}
.pick-levels{{display:flex;flex-direction:column;gap:5px;margin-bottom:8px;}}
.level-row{{display:grid;grid-template-columns:80px 1fr;gap:6px;align-items:baseline;}}
.level-lbl{{font-family:var(--mono);font-size:8px;text-transform:uppercase;letter-spacing:.1em;color:var(--mu);}}
.level-val{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.level-val.entry{{color:var(--b);}}
.level-val.sl{{color:var(--r);}}
.level-val.t1{{color:#86efac;}}
.level-val.t2{{color:var(--g);}}
.level-val.t3{{color:var(--y);}}
.level-pct{{font-size:10px;color:var(--mu);}}
.level-trigger{{font-family:var(--mono);font-size:9px;color:var(--y);grid-column:1/-1;padding-left:86px;}}
.timing-row{{font-family:var(--mono);font-size:9px;color:#4a7090;padding:2px 0;}}
.mb-badge{{font-family:var(--mono);font-size:9px;color:var(--y);
  background:rgba(245,200,66,.1);border:1px solid rgba(245,200,66,.2);
  padding:4px 8px;border-radius:4px;margin:6px 0;display:inline-block;}}
.pick-patterns{{display:flex;flex-wrap:wrap;gap:3px;margin-top:8px;}}
.no-picks{{font-family:var(--mono);font-size:11px;color:var(--mu);
  text-align:center;padding:20px;border:1px dashed var(--b2);border-radius:8px;}}

/* SECTOR BARS */
.sector-section{{background:var(--s1);border:1px solid var(--b1);border-radius:9px;
  padding:12px 14px;margin-bottom:14px;}}
.sector-title{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;
  letter-spacing:.16em;margin-bottom:10px;}}
.sector-bars{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;}}
.sec-bar{{display:flex;flex-direction:column;gap:3px;}}
.sb-lbl{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;}}
.sb-track{{height:4px;background:var(--b2);border-radius:2px;overflow:hidden;}}
.sb-fill{{height:100%;border-radius:2px;}}

/* CONTROLS */
.controls{{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:8px;}}
.ctrl-lbl{{font-family:var(--mono);font-size:8px;color:var(--mu);letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;}}
.fb{{padding:5px 11px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);
  color:var(--mu);font-family:var(--mono);font-size:9px;letter-spacing:.07em;cursor:pointer;
  transition:all .13s;text-transform:uppercase;white-space:nowrap;}}
.fb:hover,.fb.on{{border-color:var(--b);color:var(--b);background:rgba(45,127,249,.07);}}
.fb.on-mb{{border-color:var(--y)!important;color:var(--y)!important;background:rgba(245,200,66,.08)!important;}}
.si{{padding:6px 12px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);
  color:var(--tx);font-family:var(--mono);font-size:11px;outline:none;min-width:140px;}}
.si:focus{{border-color:var(--b);}}
.si::placeholder{{color:var(--mu);}}

/* TABLE */
.tbl-head{{display:grid;grid-template-columns:36px 130px 68px 1fr 100px 120px 68px 100px 24px;
  gap:6px;padding:6px 11px;font-family:var(--mono);font-size:7px;text-transform:uppercase;
  letter-spacing:.12em;color:var(--mu);border-bottom:1px solid var(--b1);margin-bottom:3px;}}
.results{{display:flex;flex-direction:column;gap:4px;}}
.result-row{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;overflow:hidden;}}
.row-main{{display:grid;grid-template-columns:36px 130px 68px 1fr 100px 120px 68px 100px 24px;
  gap:6px;padding:8px 11px;align-items:center;cursor:pointer;transition:background .13s;}}
.row-main:hover{{background:var(--s2);}}
.rank{{font-family:var(--dis);font-size:10px;color:var(--mu);text-align:center;}}
.sym{{font-family:var(--dis);font-size:13px;font-weight:700;color:#fff;letter-spacing:.04em;}}
.mb-inline{{font-size:10px;margin-left:3px;}}
.sec-tag{{font-family:var(--mono);font-size:8px;color:var(--mu);margin-top:1px;}}
.score{{font-family:var(--dis);font-size:17px;font-weight:900;}}
.col-chips{{display:flex;flex-wrap:wrap;gap:2px;}}
.chip{{font-family:var(--mono);font-size:8px;padding:2px 5px;border-radius:3px;font-weight:600;white-space:nowrap;}}
.cb{{background:rgba(0,229,160,.1);color:#00e5a0;border:1px solid rgba(0,229,160,.18);}}
.cr{{background:rgba(245,96,96,.1);color:#f56060;border:1px solid rgba(245,96,96,.18);}}
.cn{{background:rgba(245,200,66,.08);color:#f5c842;border:1px solid rgba(245,200,66,.14);}}
.col-price{{text-align:right;}}
.price{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.pct-chg{{font-family:var(--mono);font-size:9px;margin-top:1px;}}
.sent-badge{{padding:4px 8px;border-radius:5px;font-family:var(--dis);font-size:8px;font-weight:700;text-align:center;white-space:nowrap;}}
.vol-c{{font-family:var(--mono);font-size:9px;text-align:right;}}
.ts-preview{{font-family:var(--mono);font-size:9px;text-align:right;}}
.expand-icon{{color:var(--mu);font-size:9px;text-align:center;transition:transform .17s;}}

/* DETAIL PANEL */
.row-detail{{border-top:1px solid var(--b1);padding:12px 11px;background:rgba(4,6,12,.65);}}
.detail-3col{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}}
@media(max-width:900px){{.detail-3col{{grid-template-columns:1fr;}}
  .tbl-head,.row-main{{grid-template-columns:36px 1fr 60px 1fr 90px;}}}}
.detail-title{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.12em;margin-bottom:7px;}}
.sig-list{{display:flex;flex-direction:column;gap:5px;margin-bottom:10px;}}
.sig-row{{display:flex;gap:6px;align-items:flex-start;font-family:var(--mono);font-size:10px;line-height:1.5;}}
.mini-stats{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
.ms-card{{background:var(--s2);border:1px solid var(--b1);border-radius:4px;padding:6px 8px;}}
.ms-lbl{{font-family:var(--mono);font-size:7px;color:var(--mu);text-transform:uppercase;letter-spacing:.1em;margin-bottom:1px;}}
.ms-val{{font-family:var(--mono);font-size:11px;font-weight:600;}}

/* TRADE SETUP BOX */
.trade-setup-box{{background:rgba(8,12,24,.8);border:1px solid var(--b2);border-radius:7px;overflow:hidden;}}
.ts-header{{padding:7px 11px;border-bottom:1px solid var(--b1);display:flex;align-items:center;
  gap:8px;font-family:var(--mono);font-size:10px;flex-wrap:wrap;}}
.ts-trigger{{font-family:var(--mono);font-size:9px;color:var(--y);flex:1;}}
.ts-levels{{padding:8px 11px;display:flex;flex-direction:column;gap:5px;}}
.ts-row{{display:grid;grid-template-columns:90px 1fr;gap:6px;align-items:center;}}
.tsl{{font-family:var(--mono);font-size:8px;text-transform:uppercase;letter-spacing:.1em;color:var(--mu);}}
.tsv{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.entry-l{{color:var(--b)!important;}} .tsv.t1-v{{color:#86efac;}} .tsv.t2-v{{color:var(--g);}}
.tsv.t3-v{{color:var(--y);}} .tsv.sl-v{{color:var(--r);}}
.timing-row{{font-family:var(--mono);font-size:9px;color:#3a5a70;padding:2px 11px;}}

/* MULTIBAGGER DETAIL */
.mb-detail-box{{background:rgba(20,16,4,.7);border:1px solid rgba(245,200,66,.2);
  border-radius:7px;overflow:hidden;}}
.mb-detail-header{{padding:7px 11px;border-bottom:1px solid rgba(245,200,66,.15);
  font-family:var(--mono);font-size:9px;color:var(--y);letter-spacing:.1em;text-transform:uppercase;}}
.mb-reason{{font-family:var(--mono);font-size:10px;color:#7a6030;padding:3px 11px;line-height:1.6;}}
.mb-stats{{display:flex;gap:12px;padding:7px 11px;flex-wrap:wrap;
  font-family:var(--mono);font-size:9px;color:#4a4020;border-top:1px solid rgba(245,200,66,.1);}}

.err-note{{font-family:var(--mono);font-size:9px;color:#304560;padding:6px 10px;margin-top:6px;}}
.dis{{text-align:center;font-family:var(--mono);font-size:8px;color:#0d1820;
  margin-top:28px;line-height:2;letter-spacing:.04em;}}
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-track{{background:var(--b1);}}
::-webkit-scrollbar-thumb{{background:var(--b2);border-radius:2px;}}
</style>
</head>
<body>
<div class="wrap">

<div class="hdr">
  <div class="badge"><span class="dot"></span>NSE F&O · SMC + ENTRY/SL/TARGET + MULTIBAGGER</div>
  <h1>NSE F&O SMART MONEY SCANNER</h1>
  <div class="hdr-sub">BOS · CHoCH · Order Blocks · FVG · Liquidity Grabs · ATR Entry/SL · Multibagger Detection</div>
  <div class="scan-meta">
    <div class="meta-item">SCANNED <span>{len(valid)}</span></div>
    <div class="meta-item">MULTIBAGGERS <span>{mbs_count}</span></div>
    <div class="meta-item">MODE <span>{mode_str}</span></div>
    <div class="meta-item">GENERATED <span>{scan_time}</span></div>
  </div>
</div>

<div class="stats">
  {''.join(f'<div class="stat"><div class="stat-lbl">{l}</div><div class="stat-val" style="color:{c}">{v}</div></div>' for l,v,c in [
    ("Scanned",len(valid),"var(--b)"),("Bullish",bull,"var(--g)"),("Bearish",bear,"var(--r)"),
    ("Strong Bull",strong,"var(--y)"),("Multibaggers",mbs_count,"#f5c842"),
    ("Avg Score",f"{avg_sc:+d}","var(--g)" if avg_sc>=0 else "var(--r)")])}
</div>

{weekly_html}

<div class="sector-section">
  <div class="sector-title">⚡ SECTOR SMART MONEY FLOW</div>
  <div class="sector-bars">{sector_bars}</div>
</div>

<div class="controls">
  <span class="ctrl-lbl">Filter:</span>
  <button class="fb on" onclick="filterSent(this,'ALL')">ALL</button>
  <button class="fb" onclick="filterSent(this,'BULL')">BULL</button>
  <button class="fb" onclick="filterSent(this,'BEAR')">BEAR</button>
  <button class="fb" onclick="filterMB(this)">💎 MULTIBAGGER</button>
  <button class="fb" onclick="filterStrong(this)">STRONG ≥50</button>
  <input class="si" placeholder="Search symbol…" oninput="searchStocks(this.value)">
  <span class="ctrl-lbl" style="margin-left:auto">Sort:</span>
  <button class="fb on" onclick="sortResults(this,'score')">Score</button>
  <button class="fb" onclick="sortResults(this,'mb')">MB Score</button>
  <button class="fb" onclick="sortResults(this,'change')">% Chg</button>
</div>
<div class="controls" style="margin-bottom:12px;gap:4px">
  <span class="ctrl-lbl">Sector:</span>
  <button class="fb on" onclick="filterSector(this,'ALL')">ALL</button>
  {sector_btns}
</div>

<div class="tbl-head">
  <div>#</div><div>STOCK</div><div>SCORE</div><div>PATTERNS</div>
  <div>PRICE</div><div>SENTIMENT</div><div>VOL</div><div>TRADE DIR/SL</div><div></div>
</div>

<div class="results" id="rc">{rows_html}</div>
{err_html}

<div class="dis">
  DATA: {mode_str} · SMC ENGINE + ATR ENTRY/SL/TARGET · MULTIBAGGER DETECTION · {len(valid)} NSE F&O STOCKS<br>
  FOR EDUCATIONAL PURPOSES ONLY · NOT SEBI REGISTERED RESEARCH · CONDUCT YOUR OWN DUE DILIGENCE
</div>
</div>

<script>
let F = {{sent:'ALL',sector:'ALL',search:'',sort:'score',strong:false,mb:false}};
function applyFilters(){{
  const rows=[...document.querySelectorAll('.result-row')];
  let vis=[];
  rows.forEach(r=>{{
    const s=r.dataset.sent,sec=r.dataset.sector,sc=parseInt(r.dataset.score),m=r.dataset.mb;
    const sym=r.querySelector('.sym').textContent.toLowerCase();
    let show=true;
    if(F.mb && m!=='1') show=false;
    else if(!F.mb && F.strong && sc<50) show=false;
    else if(!F.mb && !F.strong && F.sent!=='ALL' && s!==F.sent) show=false;
    if(F.sector!=='ALL' && sec!==F.sector) show=false;
    if(F.search && !sym.includes(F.search.toLowerCase())) show=false;
    r.style.display=show?'':'none';
    if(show) vis.push(r);
  }});
  const rc=document.getElementById('rc');
  vis.sort((a,b)=>{{
    if(F.sort==='score') return parseInt(b.dataset.score)-parseInt(a.dataset.score);
    if(F.sort==='change') return parseFloat(b.dataset.chg||0)-parseFloat(a.dataset.chg||0);
    return parseInt(b.dataset.score)-parseInt(a.dataset.score);
  }});
  vis.forEach(r=>rc.appendChild(r));
}}
function clearFBs(cls){{document.querySelectorAll(cls).forEach(b=>{{b.classList.remove('on');b.classList.remove('on-mb');}});}}
function filterSent(btn,v){{clearFBs('.controls .fb');btn.classList.add('on');F.sent=v;F.strong=false;F.mb=false;applyFilters();}}
function filterStrong(btn){{clearFBs('.controls .fb');btn.classList.add('on');F.strong=true;F.mb=false;applyFilters();}}
function filterMB(btn){{clearFBs('.controls .fb');btn.classList.add('on');btn.classList.add('on-mb');F.mb=true;F.strong=false;applyFilters();}}
function filterSector(btn,v){{document.querySelectorAll('.controls:nth-of-type(2) .fb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');F.sector=v;applyFilters();}}
function searchStocks(v){{F.search=v;applyFilters();}}
function sortResults(btn,v){{document.querySelectorAll('.controls .fb').forEach(b=>{{if(b.onclick&&b.onclick.toString().includes('sortResults'))b.classList.remove('on');}});btn.classList.add('on');F.sort=v;applyFilters();}}
function toggleRow(id){{
  const d=document.getElementById('detail-'+id);
  const ic=document.getElementById('icon-'+id);
  if(d.style.display==='none'){{d.style.display='block';ic.style.transform='rotate(180deg)';}}
  else{{d.style.display='none';ic.style.transform='';}}
}}
</script>
</body>
</html>"""
