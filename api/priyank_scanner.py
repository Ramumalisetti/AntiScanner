"""
╔══════════════════════════════════════════════════════════════════════════╗
║  PRIYANK SHARMA METHODOLOGY SCANNER — NIFTY 500                        ║
║  "HOLD with Priyank" Framework                                          ║
║                                                                          ║
║  STRATEGY IMPLEMENTED:                                                   ║
║  1. Liquidity Filter  — Market Cap > ₹10,000 Cr (institutional stocks) ║
║  2. Sector Strength   — Finds sectors with collective momentum          ║
║  3. Fake Breakout     — Trap detection with reversal confirmation       ║
║  4. Liquidity Sweep   — Smart money stop-hunt zones                     ║
║  5. EMA 9/21 Setup    — Trend confirmation + crossover entries          ║
║  6. Multi-Timeframe   — Weekly structure + Daily execution              ║
║  7. Fibonacci Targets — 1.272, 1.618 extensions for exit levels        ║
║  8. Risk-Reward       — Minimum 1:1.5, ideal 1:2                       ║
║  9. OpenRouter AI     — Final pick reasoning (free LLM)                ║
║                                                                          ║
║  USAGE:                                                                  ║
║    pip install yfinance pandas numpy requests flask                      ║
║    python priyank_scanner.py --demo                                     ║
║    python priyank_scanner.py --top 50                                   ║
║    python priyank_scanner.py --sector Banking                           ║
║    python priyank_scanner.py --serve                                    ║
║    set OPENROUTER_API_KEY=your_key   (free at openrouter.ai)            ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import argparse, json, os, random, time, webbrowser
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════
#  OPENROUTER CONFIG
# ══════════════════════════════════════════════════════════════════════
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-r1:free")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

def call_ai(prompt: str, max_tokens=1500) -> str:
    if not OPENROUTER_API_KEY:
        return None
    try:
        r = requests.post(OPENROUTER_URL, timeout=60, json={
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0.2,
        }, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/priyank-scanner",
            "X-Title": "Priyank Sharma Scanner",
        })
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        # Strip DeepSeek-R1 thinking tags
        if "</think>" in text:
            text = text[text.rfind("</think>")+8:].strip()
        return text
    except Exception as e:
        print(f"  ⚠ AI error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════
#  NIFTY 500 STOCKS — Filtered for Priyank's methodology
#  Market Cap > ₹10,000 Cr + F&O eligible preferred
# ══════════════════════════════════════════════════════════════════════
NIFTY500 = [
    # ── BANKING (High MCap, institutional) ──
    {"sym":"HDFCBANK",    "yf":"HDFCBANK.NS",    "sector":"Banking",    "mcap":1300000, "lot":550},
    {"sym":"ICICIBANK",   "yf":"ICICIBANK.NS",   "sector":"Banking",    "mcap":900000,  "lot":700},
    {"sym":"SBIN",        "yf":"SBIN.NS",        "sector":"Banking",    "mcap":730000,  "lot":1500},
    {"sym":"AXISBANK",    "yf":"AXISBANK.NS",    "sector":"Banking",    "mcap":390000,  "lot":1200},
    {"sym":"KOTAKBANK",   "yf":"KOTAKBANK.NS",   "sector":"Banking",    "mcap":380000,  "lot":400},
    {"sym":"INDUSINDBK",  "yf":"INDUSINDBK.NS",  "sector":"Banking",    "mcap":115000,  "lot":500},
    {"sym":"BANKBARODA",  "yf":"BANKBARODA.NS",  "sector":"Banking",    "mcap":135000,  "lot":5850},
    {"sym":"PNB",         "yf":"PNB.NS",         "sector":"Banking",    "mcap":120000,  "lot":8000},
    {"sym":"CANBK",       "yf":"CANBK.NS",       "sector":"Banking",    "mcap":90000,   "lot":4700},
    {"sym":"IDFCFIRSTB",  "yf":"IDFCFIRSTB.NS",  "sector":"Banking",    "mcap":55000,   "lot":10000},
    {"sym":"FEDERALBNK",  "yf":"FEDERALBNK.NS",  "sector":"Banking",    "mcap":48000,   "lot":10000},
    {"sym":"BANDHANBNK",  "yf":"BANDHANBNK.NS",  "sector":"Banking",    "mcap":33000,   "lot":5000},
    # ── FINANCE / NBFC ──
    {"sym":"BAJFINANCE",  "yf":"BAJFINANCE.NS",  "sector":"Finance",    "mcap":420000,  "lot":125},
    {"sym":"BAJAJFINSV",  "yf":"BAJAJFINSV.NS",  "sector":"Finance",    "mcap":265000,  "lot":500},
    {"sym":"SHRIRAMFIN",  "yf":"SHRIRAMFIN.NS",  "sector":"Finance",    "mcap":90000,   "lot":300},
    {"sym":"CHOLAFIN",    "yf":"CHOLAFIN.NS",    "sector":"Finance",    "mcap":85000,   "lot":500},
    {"sym":"MUTHOOTFIN",  "yf":"MUTHOOTFIN.NS",  "sector":"Finance",    "mcap":85000,   "lot":750},
    {"sym":"JIOFIN",      "yf":"JIOFIN.NS",      "sector":"Finance",    "mcap":200000,  "lot":6250},
    {"sym":"CDSL",        "yf":"CDSL.NS",        "sector":"Finance",    "mcap":30000,   "lot":600},
    {"sym":"MCX",         "yf":"MCX.NS",         "sector":"Finance",    "mcap":35000,   "lot":800},
    {"sym":"ANGELONE",    "yf":"ANGELONE.NS",    "sector":"Finance",    "mcap":25000,   "lot":500},
    {"sym":"360ONE",      "yf":"360ONE.NS",       "sector":"Finance",    "mcap":22000,   "lot":900},
    # ── INSURANCE ──
    {"sym":"SBILIFE",     "yf":"SBILIFE.NS",     "sector":"Insurance",  "mcap":180000,  "lot":750},
    {"sym":"HDFCLIFE",    "yf":"HDFCLIFE.NS",    "sector":"Insurance",  "mcap":130000,  "lot":1100},
    {"sym":"LICI",        "yf":"LICI.NS",        "sector":"Insurance",  "mcap":580000,  "lot":700},
    {"sym":"ICICIGI",     "yf":"ICICIGI.NS",     "sector":"Insurance",  "mcap":85000,   "lot":375},
    {"sym":"ICICIPRULI",  "yf":"ICICIPRULI.NS",  "sector":"Insurance",  "mcap":75000,   "lot":1500},
    {"sym":"STARHEALTH",  "yf":"STARHEALTH.NS",  "sector":"Insurance",  "mcap":42000,   "lot":1250},
    # ── IT ──
    {"sym":"TCS",         "yf":"TCS.NS",         "sector":"IT",         "mcap":890000,  "lot":175},
    {"sym":"INFY",        "yf":"INFY.NS",        "sector":"IT",         "mcap":625000,  "lot":400},
    {"sym":"HCLTECH",     "yf":"HCLTECH.NS",     "sector":"IT",         "mcap":325000,  "lot":700},
    {"sym":"WIPRO",       "yf":"WIPRO.NS",       "sector":"IT",         "mcap":270000,  "lot":1500},
    {"sym":"TECHM",       "yf":"TECHM.NS",       "sector":"IT",         "mcap":155000,  "lot":600},
    {"sym":"LTIM",        "yf":"LTIM.NS",        "sector":"IT",         "mcap":155000,  "lot":150},
    {"sym":"MPHASIS",     "yf":"MPHASIS.NS",     "sector":"IT",         "mcap":42000,   "lot":400},
    {"sym":"COFORGE",     "yf":"COFORGE.NS",     "sector":"IT",         "mcap":30000,   "lot":150},
    {"sym":"PERSISTENT",  "yf":"PERSISTENT.NS",  "sector":"IT",         "mcap":60000,   "lot":125},
    {"sym":"OFSS",        "yf":"OFSS.NS",        "sector":"IT",         "mcap":115000,  "lot":200},
    {"sym":"KPITTECH",    "yf":"KPITTECH.NS",    "sector":"IT",         "mcap":22000,   "lot":500},
    {"sym":"TATAELXSI",   "yf":"TATAELXSI.NS",   "sector":"IT",         "mcap":28000,   "lot":100},
    # ── ENERGY ──
    {"sym":"RELIANCE",    "yf":"RELIANCE.NS",    "sector":"Energy",     "mcap":1760000, "lot":250},
    {"sym":"ONGC",        "yf":"ONGC.NS",        "sector":"Energy",     "mcap":340000,  "lot":3850},
    {"sym":"BPCL",        "yf":"BPCL.NS",        "sector":"Energy",     "mcap":138000,  "lot":1800},
    {"sym":"IOC",         "yf":"IOC.NS",         "sector":"Energy",     "mcap":200000,  "lot":10500},
    {"sym":"HINDPETRO",   "yf":"HINDPETRO.NS",   "sector":"Energy",     "mcap":70000,   "lot":2700},
    {"sym":"GAIL",        "yf":"GAIL.NS",        "sector":"Energy",     "mcap":145000,  "lot":6850},
    {"sym":"IGL",         "yf":"IGL.NS",         "sector":"Energy",     "mcap":24000,   "lot":2750},
    {"sym":"MGL",         "yf":"MGL.NS",         "sector":"Energy",     "mcap":12000,   "lot":400},
    {"sym":"PETRONET",    "yf":"PETRONET.NS",     "sector":"Energy",     "mcap":38000,   "lot":3000},
    # ── POWER ──
    {"sym":"NTPC",        "yf":"NTPC.NS",        "sector":"Power",      "mcap":350000,  "lot":2700},
    {"sym":"POWERGRID",   "yf":"POWERGRID.NS",   "sector":"Power",      "mcap":295000,  "lot":3200},
    {"sym":"ADANIGREEN",  "yf":"ADANIGREEN.NS",  "sector":"Power",      "mcap":145000,  "lot":500},
    {"sym":"ADANIPOWER",  "yf":"ADANIPOWER.NS",  "sector":"Power",      "mcap":215000,  "lot":2100},
    {"sym":"TATAPOWER",   "yf":"TATAPOWER.NS",   "sector":"Power",      "mcap":140000,  "lot":3375},
    {"sym":"SUZLON",      "yf":"SUZLON.NS",      "sector":"Power",      "mcap":77000,   "lot":14000},
    {"sym":"CESC",        "yf":"CESC.NS",        "sector":"Power",      "mcap":18000,   "lot":2600},
    {"sym":"TORNTPOWER",  "yf":"TORNTPOWER.NS",  "sector":"Power",      "mcap":68000,   "lot":750},
    # ── AUTO ──
    {"sym":"MARUTI",      "yf":"MARUTI.NS",      "sector":"Auto",       "mcap":400000,  "lot":37},
    {"sym":"TATAMOTORS",  "yf":"TATAMOTORS.NS",  "sector":"Auto",       "mcap":320000,  "lot":1400},
    {"sym":"EICHERMOT",   "yf":"EICHERMOT.NS",   "sector":"Auto",       "mcap":365000,  "lot":175},
    {"sym":"HEROMOTOCO",  "yf":"HEROMOTOCO.NS",  "sector":"Auto",       "mcap":100000,  "lot":300},
    {"sym":"BAJAJ-AUTO",  "yf":"BAJAJ-AUTO.NS",  "sector":"Auto",       "mcap":295000,  "lot":125},
    {"sym":"M&M",         "yf":"M&M.NS",         "sector":"Auto",       "mcap":380000,  "lot":700},
    {"sym":"TVSMOTORS",   "yf":"TVSMOTORS.NS",   "sector":"Auto",       "mcap":115000,  "lot":350},
    {"sym":"ASHOKLEY",    "yf":"ASHOKLEY.NS",     "sector":"Auto",       "mcap":68000,   "lot":5500},
    {"sym":"APOLLOTYRE",  "yf":"APOLLOTYRE.NS",  "sector":"Auto",       "mcap":28000,   "lot":3500},
    {"sym":"BALKRISIND",  "yf":"BALKRISIND.NS",  "sector":"Auto",       "mcap":38000,   "lot":400},
    {"sym":"MOTHERSON",   "yf":"MOTHERSON.NS",   "sector":"Auto",       "mcap":88000,   "lot":9000},
    {"sym":"BHARATFORG",  "yf":"BHARATFORG.NS",  "sector":"Auto",       "mcap":42000,   "lot":1000},
    {"sym":"EXIDEIND",    "yf":"EXIDEIND.NS",    "sector":"Auto",       "mcap":26000,   "lot":3600},
    # ── PHARMA ──
    {"sym":"SUNPHARMA",   "yf":"SUNPHARMA.NS",   "sector":"Pharma",     "mcap":420000,  "lot":700},
    {"sym":"DRREDDY",     "yf":"DRREDDY.NS",     "sector":"Pharma",     "mcap":105000,  "lot":125},
    {"sym":"CIPLA",       "yf":"CIPLA.NS",       "sector":"Pharma",     "mcap":125000,  "lot":650},
    {"sym":"DIVISLAB",    "yf":"DIVISLAB.NS",    "sector":"Pharma",     "mcap":132000,  "lot":200},
    {"sym":"AUROPHARMA",  "yf":"AUROPHARMA.NS",  "sector":"Pharma",     "mcap":81000,   "lot":650},
    {"sym":"LUPIN",       "yf":"LUPIN.NS",       "sector":"Pharma",     "mcap":105000,  "lot":425},
    {"sym":"BIOCON",      "yf":"BIOCON.NS",      "sector":"Pharma",     "mcap":38000,   "lot":2600},
    {"sym":"TORNTPHARM",  "yf":"TORNTPHARM.NS",  "sector":"Pharma",     "mcap":56000,   "lot":500},
    {"sym":"ALKEM",       "yf":"ALKEM.NS",       "sector":"Pharma",     "mcap":32000,   "lot":150},
    {"sym":"GLENMARK",    "yf":"GLENMARK.NS",    "sector":"Pharma",     "mcap":38000,   "lot":1050},
    {"sym":"IPCALAB",     "yf":"IPCALAB.NS",     "sector":"Pharma",     "mcap":22000,   "lot":700},
    {"sym":"ABBOTINDIA",  "yf":"ABBOTINDIA.NS",  "sector":"Pharma",     "mcap":42000,   "lot":40},
    # ── HEALTHCARE ──
    {"sym":"APOLLOHOSP",  "yf":"APOLLOHOSP.NS",  "sector":"Healthcare", "mcap":110000,  "lot":175},
    {"sym":"MAXHEALTH",   "yf":"MAXHEALTH.NS",   "sector":"Healthcare", "mcap":35000,   "lot":700},
    {"sym":"FORTIS",      "yf":"FORTIS.NS",      "sector":"Healthcare", "mcap":32000,   "lot":3500},
    {"sym":"MEDANTA",     "yf":"MEDANTA.NS",     "sector":"Healthcare", "mcap":22000,   "lot":700},
    # ── METAL ──
    {"sym":"TATASTEEL",   "yf":"TATASTEEL.NS",   "sector":"Metal",      "mcap":195000,  "lot":5500},
    {"sym":"JSWSTEEL",    "yf":"JSWSTEEL.NS",    "sector":"Metal",      "mcap":320000,  "lot":1350},
    {"sym":"HINDALCO",    "yf":"HINDALCO.NS",    "sector":"Metal",      "mcap":230000,  "lot":2800},
    {"sym":"COALINDIA",   "yf":"COALINDIA.NS",   "sector":"Metal",      "mcap":290000,  "lot":4200},
    {"sym":"VEDL",        "yf":"VEDL.NS",        "sector":"Metal",      "mcap":112000,  "lot":2800},
    {"sym":"SAIL",        "yf":"SAIL.NS",        "sector":"Metal",      "mcap":47000,   "lot":9500},
    {"sym":"NATIONALUM",  "yf":"NATIONALUM.NS",  "sector":"Metal",      "mcap":40000,   "lot":12500},
    {"sym":"NMDC",        "yf":"NMDC.NS",        "sector":"Metal",      "mcap":27000,   "lot":5500},
    {"sym":"APLAPOLLO",   "yf":"APLAPOLLO.NS",   "sector":"Metal",      "mcap":28000,   "lot":750},
    {"sym":"JINDALSTEL",  "yf":"JINDALSTEL.NS",  "sector":"Metal",      "mcap":32000,   "lot":750},
    # ── FMCG ──
    {"sym":"HINDUNILVR",  "yf":"HINDUNILVR.NS",  "sector":"FMCG",       "mcap":535000,  "lot":300},
    {"sym":"ITC",         "yf":"ITC.NS",         "sector":"FMCG",       "mcap":580000,  "lot":3200},
    {"sym":"NESTLEIND",   "yf":"NESTLEIND.NS",   "sector":"FMCG",       "mcap":140000,  "lot":40},
    {"sym":"TATACONSUM",  "yf":"TATACONSUM.NS",  "sector":"FMCG",       "mcap":115000,  "lot":1100},
    {"sym":"MARICO",      "yf":"MARICO.NS",      "sector":"FMCG",       "mcap":103000,  "lot":2000},
    {"sym":"DABUR",       "yf":"DABUR.NS",       "sector":"FMCG",       "mcap":97000,   "lot":2750},
    {"sym":"GODREJCP",    "yf":"GODREJCP.NS",    "sector":"FMCG",       "mcap":112000,  "lot":1000},
    {"sym":"COLPAL",      "yf":"COLPAL.NS",      "sector":"FMCG",       "mcap":57000,   "lot":700},
    {"sym":"EMAMILTD",    "yf":"EMAMILTD.NS",    "sector":"FMCG",       "mcap":28000,   "lot":1200},
    {"sym":"VBL",         "yf":"VBL.NS",         "sector":"FMCG",       "mcap":96000,   "lot":500},
    {"sym":"RADICO",      "yf":"RADICO.NS",      "sector":"FMCG",       "mcap":18000,   "lot":800},
    {"sym":"UBL",         "yf":"UBL.NS",         "sector":"FMCG",       "mcap":28000,   "lot":700},
    # ── INFRA / REALTY ──
    {"sym":"LT",          "yf":"LT.NS",          "sector":"Infra",      "mcap":500000,  "lot":175},
    {"sym":"ADANIENT",    "yf":"ADANIENT.NS",    "sector":"Infra",      "mcap":280000,  "lot":1250},
    {"sym":"ADANIPORTS",  "yf":"ADANIPORTS.NS",  "sector":"Infra",      "mcap":375000,  "lot":1250},
    {"sym":"DLF",         "yf":"DLF.NS",         "sector":"Realty",     "mcap":148000,  "lot":1650},
    {"sym":"GODREJPROP",  "yf":"GODREJPROP.NS",  "sector":"Realty",     "mcap":72000,   "lot":650},
    {"sym":"OBEROIRLTY",  "yf":"OBEROIRLTY.NS",  "sector":"Realty",     "mcap":59000,   "lot":700},
    {"sym":"PRESTIGE",    "yf":"PRESTIGE.NS",    "sector":"Realty",     "mcap":58000,   "lot":800},
    {"sym":"PHOENIXLTD",  "yf":"PHOENIXLTD.NS",  "sector":"Realty",     "mcap":42000,   "lot":400},
    {"sym":"SOBHA",       "yf":"SOBHA.NS",       "sector":"Realty",     "mcap":16000,   "lot":750},
    # ── CEMENT ──
    {"sym":"ULTRACEMCO",  "yf":"ULTRACEMCO.NS",  "sector":"Cement",     "mcap":340000,  "lot":100},
    {"sym":"GRASIM",      "yf":"GRASIM.NS",      "sector":"Cement",     "mcap":185000,  "lot":475},
    {"sym":"AMBUJACEM",   "yf":"AMBUJACEM.NS",   "sector":"Cement",     "mcap":110000,  "lot":2500},
    {"sym":"ACC",         "yf":"ACC.NS",         "sector":"Cement",     "mcap":26000,   "lot":375},
    {"sym":"SHREECEM",    "yf":"SHREECEM.NS",    "sector":"Cement",     "mcap":86000,   "lot":25},
    {"sym":"DALMIACEM",   "yf":"DALMIACEM.NS",   "sector":"Cement",     "mcap":22000,   "lot":375},
    # ── TELECOM ──
    {"sym":"BHARTIARTL",  "yf":"BHARTIARTL.NS",  "sector":"Telecom",    "mcap":560000,  "lot":950},
    {"sym":"INDUSTOWER",  "yf":"INDUSTOWER.NS",  "sector":"Telecom",    "mcap":68000,   "lot":2800},
    # ── CONSUMER / RETAIL ──
    {"sym":"TITAN",       "yf":"TITAN.NS",       "sector":"Consumer",   "mcap":300000,  "lot":425},
    {"sym":"ASIANPAINT",  "yf":"ASIANPAINT.NS",  "sector":"Consumer",   "mcap":215000,  "lot":300},
    {"sym":"TRENT",       "yf":"TRENT.NS",       "sector":"Retail",     "mcap":220000,  "lot":275},
    {"sym":"DMART",       "yf":"DMART.NS",       "sector":"Retail",     "mcap":265000,  "lot":350},
    {"sym":"ZOMATO",      "yf":"ZOMATO.NS",      "sector":"Retail",     "mcap":225000,  "lot":3750},
    {"sym":"NYKAA",       "yf":"NYKAA.NS",       "sector":"Retail",     "mcap":27000,   "lot":2800},
    {"sym":"JUBLFOOD",    "yf":"JUBLFOOD.NS",    "sector":"Retail",     "mcap":30000,   "lot":1000},
    {"sym":"PAGEIND",     "yf":"PAGEIND.NS",     "sector":"Consumer",   "mcap":35000,   "lot":30},
    {"sym":"HAVELLS",     "yf":"HAVELLS.NS",     "sector":"Consumer",   "mcap":103000,  "lot":500},
    {"sym":"VOLTAS",      "yf":"VOLTAS.NS",      "sector":"Consumer",   "mcap":42000,   "lot":700},
    # ── CHEMICAL ──
    {"sym":"PIDILITIND",  "yf":"PIDILITIND.NS",  "sector":"Chemical",   "mcap":160000,  "lot":250},
    {"sym":"SRF",         "yf":"SRF.NS",         "sector":"Chemical",   "mcap":56000,   "lot":375},
    {"sym":"AARTIIND",    "yf":"AARTIIND.NS",    "sector":"Chemical",   "mcap":18000,   "lot":1000},
    {"sym":"DEEPAKNTR",   "yf":"DEEPAKNTR.NS",   "sector":"Chemical",   "mcap":43000,   "lot":500},
    {"sym":"NAVINFLUOR",  "yf":"NAVINFLUOR.NS",  "sector":"Chemical",   "mcap":18000,   "lot":200},
    {"sym":"TATACHEM",    "yf":"TATACHEM.NS",    "sector":"Chemical",   "mcap":28000,   "lot":800},
    # ── DEFENCE / PSU ──
    {"sym":"BEL",         "yf":"BEL.NS",         "sector":"Defence",    "mcap":151000,  "lot":3500},
    {"sym":"HAL",         "yf":"HAL.NS",         "sector":"Defence",    "mcap":139000,  "lot":300},
    {"sym":"COCHINSHIP",  "yf":"COCHINSHIP.NS",  "sector":"Defence",    "mcap":24000,   "lot":350},
    {"sym":"BHEL",        "yf":"BHEL.NS",        "sector":"Defence",    "mcap":130000,  "lot":5500},
    {"sym":"IRCTC",       "yf":"IRCTC.NS",       "sector":"PSU",        "mcap":46000,   "lot":2500},
    {"sym":"IRFC",        "yf":"IRFC.NS",        "sector":"PSU",        "mcap":81000,   "lot":4800},
    {"sym":"PFC",         "yf":"PFC.NS",         "sector":"PSU",        "mcap":150000,  "lot":2700},
    {"sym":"REC",         "yf":"REC.NS",         "sector":"PSU",        "mcap":157000,  "lot":2700},
    {"sym":"RVNL",        "yf":"RVNL.NS",        "sector":"PSU",        "mcap":78000,   "lot":3500},
    {"sym":"HUDCO",       "yf":"HUDCO.NS",       "sector":"PSU",        "mcap":40000,   "lot":5000},
    {"sym":"NBCC",        "yf":"NBCC.NS",        "sector":"PSU",        "mcap":18000,   "lot":7500},
    # ── CAPITAL GOODS ──
    {"sym":"SIEMENS",     "yf":"SIEMENS.NS",     "sector":"CapGoods",   "mcap":255000,  "lot":275},
    {"sym":"ABB",         "yf":"ABB.NS",         "sector":"CapGoods",   "mcap":155000,  "lot":175},
    {"sym":"CUMMINSIND",  "yf":"CUMMINSIND.NS",  "sector":"CapGoods",   "mcap":55000,   "lot":350},
    {"sym":"THERMAX",     "yf":"THERMAX.NS",     "sector":"CapGoods",   "mcap":32000,   "lot":175},
    {"sym":"GMRINFRA",    "yf":"GMRINFRA.NS",    "sector":"Infra",      "mcap":44000,   "lot":22500},
    {"sym":"IRB",         "yf":"IRB.NS",         "sector":"Infra",      "mcap":15000,   "lot":11500},
    # ── AGRI / MISC ──
    {"sym":"UPL",         "yf":"UPL.NS",         "sector":"Agri",       "mcap":38000,   "lot":2000},
    {"sym":"PIIND",       "yf":"PIIND.NS",       "sector":"Agri",       "mcap":15000,   "lot":250},
    {"sym":"COROMANDEL",  "yf":"COROMANDEL.NS",  "sector":"Agri",       "mcap":33000,   "lot":500},
    {"sym":"JSWINFRA",    "yf":"JSWINFRA.NS",    "sector":"Infra",      "mcap":62000,   "lot":2000},
    {"sym":"PAYTM",       "yf":"PAYTM.NS",       "sector":"FinTech",    "mcap":52000,   "lot":3750},
    {"sym":"POLICYBZR",   "yf":"POLICYBZR.NS",   "sector":"FinTech",    "mcap":42000,   "lot":1000},
    {"sym":"HDFCAMC",     "yf":"HDFCAMC.NS",     "sector":"Finance",    "mcap":95000,   "lot":300},
    {"sym":"MFSL",        "yf":"MFSL.NS",        "sector":"Finance",    "mcap":25000,   "lot":400},
]

# Demo price map
PRICE_MAP = {
    "HDFCBANK":1680,"ICICIBANK":1280,"SBIN":820,"AXISBANK":1180,"KOTAKBANK":1900,
    "INDUSINDBK":1450,"BANKBARODA":260,"PNB":105,"CANBK":130,"IDFCFIRSTB":72,
    "FEDERALBNK":195,"BANDHANBNK":205,"BAJFINANCE":6800,"BAJAJFINSV":1680,
    "SHRIRAMFIN":950,"CHOLAFIN":1640,"MUTHOOTFIN":2100,"JIOFIN":320,"CDSL":1230,
    "MCX":6500,"ANGELONE":2800,"360ONE":940,"SBILIFE":1810,"HDFCLIFE":600,
    "LICI":920,"ICICIGI":1760,"ICICIPRULI":535,"STARHEALTH":430,"TCS":2450,
    "INFY":1560,"HCLTECH":1200,"WIPRO":620,"TECHM":1550,"LTIM":5200,
    "MPHASIS":2240,"COFORGE":1165,"PERSISTENT":4820,"OFSS":9780,"KPITTECH":778,
    "TATAELXSI":6200,"RELIANCE":1310,"ONGC":270,"BPCL":320,"IOC":145,
    "HINDPETRO":370,"GAIL":210,"IGL":168,"MGL":1100,"PETRONET":315,
    "NTPC":360,"POWERGRID":320,"ADANIGREEN":1310,"ADANIPOWER":560,
    "TATAPOWER":445,"SUZLON":55,"CESC":145,"TORNTPOWER":890,"MARUTI":13400,
    "TATAMOTORS":950,"EICHERMOT":13400,"HEROMOTOCO":5020,"BAJAJ-AUTO":10060,
    "M&M":3080,"TVSMOTORS":2400,"ASHOKLEY":240,"APOLLOTYRE":455,"BALKRISIND":2400,
    "MOTHERSON":165,"BHARATFORG":1380,"EXIDEIND":360,"SUNPHARMA":1800,
    "DRREDDY":6200,"CIPLA":1540,"DIVISLAB":6610,"AUROPHARMA":1385,"LUPIN":2200,
    "BIOCON":290,"TORNTPHARM":3300,"ALKEM":5320,"GLENMARK":1350,"IPCALAB":1560,
    "ABBOTINDIA":32000,"APOLLOHOSP":7690,"MAXHEALTH":1000,"FORTIS":940,
    "MEDANTA":1100,"TATASTEEL":155,"JSWSTEEL":1255,"HINDALCO":1040,
    "COALINDIA":475,"VEDL":302,"SAIL":120,"NATIONALUM":190,"NMDC":89,
    "APLAPOLLO":1200,"JINDALSTEL":820,"HINDUNILVR":2350,"ITC":465,
    "NESTLEIND":1460,"TATACONSUM":1150,"MARICO":790,"DABUR":455,"GODREJCP":1100,
    "COLPAL":2750,"EMAMILTD":710,"VBL":580,"RADICO":2100,"UBL":1850,"LT":3650,
    "ADANIENT":2480,"ADANIPORTS":1740,"DLF":600,"GODREJPROP":2800,
    "OBEROIRLTY":1660,"PRESTIGE":1435,"PHOENIXLTD":1680,"SOBHA":1220,
    "ULTRACEMCO":11780,"GRASIM":2850,"AMBUJACEM":438,"ACC":1390,"SHREECEM":28000,
    "DALMIACEM":1640,"BHARTIARTL":1820,"INDUSTOWER":340,"TITAN":3400,
    "ASIANPAINT":2250,"TRENT":6200,"DMART":4310,"ZOMATO":245,"NYKAA":155,
    "JUBLFOOD":472,"PAGEIND":42000,"HAVELLS":1650,"VOLTAS":1340,"PIDILITIND":3200,
    "SRF":2500,"AARTIIND":420,"DEEPAKNTR":1740,"NAVINFLUOR":3400,"TATACHEM":990,
    "BEL":434,"HAL":4640,"COCHINSHIP":1520,"BHEL":382,"IRCTC":572,"IRFC":106,
    "PFC":470,"REC":490,"RVNL":300,"HUDCO":210,"NBCC":95,"SIEMENS":7200,
    "ABB":7274,"CUMMINSIND":3200,"THERMAX":3400,"GMRINFRA":78,"IRB":58,
    "UPL":520,"PIIND":3010,"COROMANDEL":1900,"JSWINFRA":310,"PAYTM":780,
    "POLICYBZR":1580,"HDFCAMC":4200,"MFSL":1020,
}


# ══════════════════════════════════════════════════════════════════════
#  DATA FETCH
# ══════════════════════════════════════════════════════════════════════
def fetch_ohlcv(yf_sym: str, days: int = 90) -> pd.DataFrame:
    if not YF_AVAILABLE:
        raise ImportError("yfinance not installed")
    df = yf.Ticker(yf_sym).history(period=f"{days}d", interval="1d", auto_adjust=True)
    if df.empty or len(df) < 20:
        raise ValueError("Insufficient data")
    df = df[["Open","High","Low","Close","Volume"]].copy()
    df.columns = ["open","high","low","close","volume"]
    return df.dropna().reset_index(drop=True)


def demo_ohlcv(sym: str, days=90) -> pd.DataFrame:
    rng = random.Random(hash(sym) % 99991)
    np_rng = np.random.default_rng(hash(sym) % 99991)
    bp = float(PRICE_MAP.get(sym, rng.uniform(100, 3000)))
    closes, trend = [bp], rng.uniform(-0.001, 0.002)
    for _ in range(days-1):
        closes.append(max(closes[-1]*(1+np_rng.normal(trend, 0.013)), bp*0.3))
    rows = []
    for c in closes:
        sp = c * rng.uniform(0.007, 0.025)
        h = c + sp*rng.uniform(0.4,1.0); l = c - sp*rng.uniform(0.4,1.0)
        rows.append({"open":rng.uniform(l,h),"high":h,"low":l,"close":c,
                     "volume":int(rng.uniform(300_000,8_000_000))})
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════
#  TECHNICAL HELPERS
# ══════════════════════════════════════════════════════════════════════
def ema(closes, p):
    if len(closes) < p: return float(closes[-1])
    k = 2/(p+1); e = float(closes[-p])
    for v in closes[-p+1:]: e = v*k + e*(1-k)
    return round(e,2)

def rsi(closes, p=14):
    if len(closes) < p+2: return 50.0
    d = np.diff(closes[-p*2:])
    g = np.where(d>0,d,0.0); lo = np.where(d<0,-d,0.0)
    ag,al = g[-p:].mean(), lo[-p:].mean()
    if al==0: return 100.0
    return round(100-100/(1+ag/al),1)

def atr(df, p=14):
    h,l,c = df["high"].values, df["low"].values, df["close"].values
    trs = [max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(df))]
    return float(np.mean(trs[-p:])) if trs else c[-1]*0.018

def fibonacci_targets(swing_low, swing_high, direction="up"):
    """Fibonacci extension targets — Priyank uses 1.272 and 1.618"""
    rng = swing_high - swing_low
    if direction == "up":
        return {
            "fib_618":  round(swing_high + rng*0.618, 2),
            "fib_1000": round(swing_high + rng*1.000, 2),
            "fib_1272": round(swing_high + rng*1.272, 2),
            "fib_1618": round(swing_high + rng*1.618, 2),
        }
    else:
        return {
            "fib_618":  round(swing_low - rng*0.618, 2),
            "fib_1000": round(swing_low - rng*1.000, 2),
            "fib_1272": round(swing_low - rng*1.272, 2),
            "fib_1618": round(swing_low - rng*1.618, 2),
        }

def swing_points(df, lookback=20):
    h = df["high"].values; l = df["low"].values
    recent_H = h[-lookback:].max(); recent_L = l[-lookback:].min()
    # Find the index positions
    hi_idx = len(h) - lookback + h[-lookback:].argmax()
    lo_idx = len(l) - lookback + l[-lookback:].argmin()
    return recent_H, recent_L, hi_idx, lo_idx


# ══════════════════════════════════════════════════════════════════════
#  PRIYANK SHARMA ANALYSIS ENGINE
#  Implements all 5 strategies from his methodology
# ══════════════════════════════════════════════════════════════════════
def priyank_analyze(df: pd.DataFrame, stock: dict) -> dict:
    """
    Full Priyank Sharma methodology:
    1. Liquidity check (market cap filter)
    2. EMA 9/21 trend setup
    3. Fake Breakout / Trap detection
    4. Liquidity Sweep (stop-hunt zones)
    5. Fibonacci extension targets
    6. RR calculation (min 1:1.5)
    7. MTF context (weekly structure from daily data)
    """
    if df is None or len(df) < 30:
        return None

    c = df["close"].values; h = df["high"].values
    l = df["low"].values;   v = df["volume"].values; o = df["open"].values
    n = len(df)

    # ── 1. MARKET CAP FILTER (Priyank: >₹1,00,000 Cr for best conviction) ──
    mcap = stock.get("mcap", 0)
    mcap_grade = "A" if mcap >= 100000 else "B" if mcap >= 30000 else "C"
    # Don't skip — just flag it (user might still want to trade B/C)

    # ── 2. EMA SETUP (9 & 21) ──
    ema9  = ema(c, 9)
    ema21 = ema(c, 21)
    ema50 = ema(c, 50)
    price = float(c[-1])
    ema9_prev  = ema(c[:-1], 9)
    ema21_prev = ema(c[:-1], 21)

    # EMA crossover — Priyank enters on 9 crossing 21
    ema_bull_cross = ema9_prev < ema21_prev and ema9 > ema21  # fresh bullish cross
    ema_bear_cross = ema9_prev > ema21_prev and ema9 < ema21  # fresh bearish cross
    ema_bull_trend = ema9 > ema21 > ema50                     # strong uptrend
    ema_bear_trend = ema9 < ema21 < ema50                     # strong downtrend
    price_above_ema21 = price > ema21

    # ── 3. FAKE BREAKOUT / TRAP DETECTION ──
    # Pattern: Price breaks key level, traps traders, then reverses
    recent_high = float(h[-20:-1].max())
    recent_low  = float(l[-20:-1].min())
    last_candle = {"o":o[-1],"h":h[-1],"l":l[-1],"c":c[-1],"v":v[-1]}
    prev_candle = {"o":o[-2],"h":h[-2],"l":l[-2],"c":c[-2],"v":v[-2]}

    # Bullish fake breakout: price broke below recent low (stop hunt) then closed back above
    bull_fake_bo = (
        l[-1] < recent_low and          # wicked below key level
        c[-1] > recent_low and          # but closed back above
        c[-1] > o[-1] and               # bullish close
        v[-1] > np.mean(v[-10:]) * 1.3  # with volume
    )
    # Bearish fake breakout: price broke above recent high then closed back below
    bear_fake_bo = (
        h[-1] > recent_high and         # wicked above key level
        c[-1] < recent_high and         # but closed back below
        c[-1] < o[-1] and               # bearish close
        v[-1] > np.mean(v[-10:]) * 1.3  # with volume
    )

    # ── 4. LIQUIDITY SWEEP (Smart Money Stop Hunt) ──
    # Priyank looks for equal highs/lows where stops are parked
    avg_vol = float(np.mean(v[-20:]))
    vol_ratio = float(v[-1] / avg_vol) if avg_vol > 0 else 1.0

    # Identify equal highs (sell-side liquidity) in last 15 candles
    highs_15 = h[-15:]
    max_h = highs_15.max()
    equal_highs = sum(1 for x in highs_15 if abs(x - max_h)/max_h < 0.003)

    # Identify equal lows (buy-side liquidity)
    lows_15 = l[-15:]
    min_l = lows_15.min()
    equal_lows = sum(1 for x in lows_15 if abs(x - min_l)/min_l < 0.003)

    # Liquidity sweep signals
    liq_sweep_bull = (
        l[-1] < min_l and       # swept below equal lows
        c[-1] > min_l and       # recovered above
        c[-1] > o[-1]           # bullish
    )
    liq_sweep_bear = (
        h[-1] > max_h and       # swept above equal highs
        c[-1] < max_h and       # retreated below
        c[-1] < o[-1]           # bearish
    )

    # ── 5. MULTI-TIMEFRAME STRUCTURE (Weekly proxy from daily) ──
    # Use last 5 weeks of daily closes as weekly proxy
    weekly_closes = [c[max(0,i-5):i].mean() for i in range(10, n, 5)] if n >= 20 else [c[-1]]
    weekly_trend_up   = len(weekly_closes) >= 2 and weekly_closes[-1] > weekly_closes[-2]
    weekly_trend_down = len(weekly_closes) >= 2 and weekly_closes[-1] < weekly_closes[-2]

    # ── 6. RSI & MOMENTUM ──
    rsi_val = rsi(c)
    rsi_oversold  = rsi_val < 40
    rsi_overbought = rsi_val > 65
    rsi_prev_val  = rsi(c[:-3])
    rsi_divergence_bull = c[-1] < c[-5] and rsi_val > rsi_prev_val  # price lower, RSI higher

    # ── 7. SWING POINTS FOR FIBONACCI ──
    rec_h, rec_l, hi_idx, lo_idx = swing_points(df, 20)
    fib_up   = fibonacci_targets(rec_l, rec_h, "up")
    fib_down = fibonacci_targets(rec_l, rec_h, "down")

    # ── 8. ATR FOR PRECISE SL ──
    atr_val = atr(df)

    # ── 9. SCORING — Priyank style (quality signals only) ──
    score = 0
    signals = []
    direction = None

    # MCap bonus
    if mcap_grade == "A": score += 10
    elif mcap_grade == "B": score += 5

    # EMA signals (high weight in Priyank system)
    if ema_bull_cross:
        score += 35; signals.append({"sig":"EMA Cross↑","type":"BULL","weight":"HIGH",
            "desc":f"EMA9 crossed above EMA21 — fresh bullish momentum signal"})
    if ema_bear_cross:
        score -= 35; signals.append({"sig":"EMA Cross↓","type":"BEAR","weight":"HIGH",
            "desc":f"EMA9 crossed below EMA21 — fresh bearish momentum signal"})
    if ema_bull_trend and not ema_bull_cross:
        score += 15; signals.append({"sig":"EMA Uptrend","type":"BULL","weight":"MED",
            "desc":f"EMA9({ema9:.0f}) > EMA21({ema21:.0f}) > EMA50({ema50:.0f}) — strong trend"})
    if ema_bear_trend and not ema_bear_cross:
        score -= 15; signals.append({"sig":"EMA Downtrend","type":"BEAR","weight":"MED",
            "desc":f"EMA9({ema9:.0f}) < EMA21({ema21:.0f}) < EMA50({ema50:.0f}) — downtrend"})

    # Fake breakout signals (Priyank's signature — highest weight)
    if bull_fake_bo:
        score += 40; signals.append({"sig":"Fake BO↑ 🪤","type":"BULL","weight":"HIGHEST",
            "desc":f"Retail trapped short below ₹{recent_low:.2f} — smart money reversal. Vol {vol_ratio:.1f}x"})
    if bear_fake_bo:
        score -= 40; signals.append({"sig":"Fake BO↓ 🪤","type":"BEAR","weight":"HIGHEST",
            "desc":f"Retail trapped long above ₹{recent_high:.2f} — institutional reversal. Vol {vol_ratio:.1f}x"})

    # Liquidity sweep
    if liq_sweep_bull:
        score += 30; signals.append({"sig":"LiqSweep↑ 💧","type":"BULL","weight":"HIGH",
            "desc":f"Buy-side liquidity sweep below equal lows ₹{min_l:.2f} — stops hunted, reversal likely"})
    if liq_sweep_bear:
        score -= 30; signals.append({"sig":"LiqSweep↓ 💧","type":"BEAR","weight":"HIGH",
            "desc":f"Sell-side liquidity sweep above equal highs ₹{max_h:.2f} — stops hunted, reversal likely"})

    # Equal highs/lows (liquidity pools sitting)
    if equal_lows >= 3 and not liq_sweep_bull:
        score += 8; signals.append({"sig":"EqLows Pool 🎯","type":"BULL","weight":"LOW",
            "desc":f"{equal_lows} equal lows at ₹{min_l:.2f} — buy-side liquidity pool, sweep likely"})
    if equal_highs >= 3 and not liq_sweep_bear:
        score -= 8; signals.append({"sig":"EqHighs Pool 🎯","type":"BEAR","weight":"LOW",
            "desc":f"{equal_highs} equal highs at ₹{max_h:.2f} — sell-side liquidity pool, sweep likely"})

    # RSI
    if rsi_oversold:
        score += 10; signals.append({"sig":f"RSI {rsi_val} Oversold","type":"BULL","weight":"MED",
            "desc":f"RSI {rsi_val} oversold — potential mean reversion setup"})
    if rsi_overbought:
        score -= 10; signals.append({"sig":f"RSI {rsi_val} Overbought","type":"BEAR","weight":"MED",
            "desc":f"RSI {rsi_val} overbought — extended, caution on longs"})
    if rsi_divergence_bull:
        score += 15; signals.append({"sig":"RSI Divergence↑","type":"BULL","weight":"HIGH",
            "desc":f"Price lower low but RSI higher — hidden bullish divergence"})

    # MTF weekly alignment
    if weekly_trend_up:
        score += 10; signals.append({"sig":"Weekly Uptrend","type":"BULL","weight":"MED",
            "desc":"Higher timeframe (weekly) trend is bullish — trade in trend direction"})
    if weekly_trend_down:
        score -= 10; signals.append({"sig":"Weekly Downtrend","type":"BEAR","weight":"MED",
            "desc":"Higher timeframe (weekly) trend is bearish — avoid longs"})

    # Volume spike
    if vol_ratio >= 2.0:
        is_bull_vol = c[-1] > o[-1]
        score += (12 if is_bull_vol else -12)
        signals.append({"sig":f"Vol {vol_ratio:.1f}x 📊","type":"BULL" if is_bull_vol else "BEAR","weight":"MED",
            "desc":f"Institutional {'buying' if is_bull_vol else 'selling'} — {vol_ratio:.1f}x avg volume"})

    score = max(-100, min(100, round(score)))
    bull_sigs = sum(1 for s in signals if s["type"]=="BULL")
    bear_sigs = sum(1 for s in signals if s["type"]=="BEAR")
    direction = "LONG" if score >= 15 else "SHORT" if score <= -15 else None

    # ── 10. TRADE LEVELS (Priyank: min RR 1:1.5, use Fib for targets) ──
    trade = None
    if direction == "LONG":
        entry     = round(price, 2)
        sl        = round(min(rec_l - atr_val*0.2, price - atr_val*1.5), 2)
        sl_pct    = round((price-sl)/price*100, 1)
        # Priyank uses Fibonacci extensions for targets
        t1 = fib_up["fib_618"]   # conservative — 1:RR depends on SL
        t2 = fib_up["fib_1272"]  # Priyank's preferred exit
        t3 = fib_up["fib_1618"]  # extended target
        rr1 = round((t1-entry)/(entry-sl), 1) if entry > sl else 0
        rr2 = round((t2-entry)/(entry-sl), 1) if entry > sl else 0
        # Entry timing
        if ema_bull_cross:
            timing = f"ENTER NOW — EMA9/21 fresh cross. Ideal Priyank entry ✅"
        elif bull_fake_bo or liq_sweep_bull:
            timing = f"ENTER NOW — Trap/Sweep confirmed. Smart money reversal ✅"
        elif rsi_oversold:
            timing = f"ENTER on next green candle > ₹{price:.0f} ⚠️"
        else:
            timing = f"WAIT — pull back to EMA21 (₹{ema21:.0f}) for better entry ⏳"
        trade = {
            "direction":"LONG", "entry":entry,
            "sl":sl, "sl_pct":sl_pct,
            "t1":t1, "t2":t2, "t3":t3,
            "rr1":rr1, "rr2":rr2,
            "timing":timing,
            "ema9":ema9, "ema21":ema21, "ema50":ema50,
            "fib":fib_up, "rsi":rsi_val, "atr":round(atr_val,2),
            "good_rr": rr1 >= 1.5,  # Priyank minimum
        }

    elif direction == "SHORT":
        entry  = round(price, 2)
        sl     = round(max(rec_h + atr_val*0.2, price + atr_val*1.5), 2)
        sl_pct = round((sl-price)/price*100, 1)
        t1 = fib_down["fib_618"]
        t2 = fib_down["fib_1272"]
        t3 = fib_down["fib_1618"]
        rr1 = round((entry-t1)/(sl-entry), 1) if sl > entry else 0
        rr2 = round((entry-t2)/(sl-entry), 1) if sl > entry else 0
        if ema_bear_cross:
            timing = f"ENTER NOW — EMA9/21 bearish cross. Ideal short entry ✅"
        elif bear_fake_bo or liq_sweep_bear:
            timing = f"ENTER NOW — Trap confirmed above ₹{recent_high:.0f}. Short on reaction ✅"
        else:
            timing = f"WAIT — rally to EMA21 (₹{ema21:.0f}) for better short entry ⏳"
        trade = {
            "direction":"SHORT", "entry":entry,
            "sl":sl, "sl_pct":sl_pct,
            "t1":t1, "t2":t2, "t3":t3,
            "rr1":rr1, "rr2":rr2,
            "timing":timing,
            "ema9":ema9, "ema21":ema21, "ema50":ema50,
            "fib":fib_down, "rsi":rsi_val, "atr":round(atr_val,2),
            "good_rr": rr1 >= 1.5,
        }

    pct_chg = ((c[-1]-c[-2])/c[-2]*100) if len(c)>1 else 0
    w52h = float(h[-min(252,n):].max())
    w52l = float(l[-min(252,n):].min())
    pos52 = round((price-w52l)/max(w52h-w52l,1)*100,1)

    return {
        "score": score,
        "direction": direction,
        "signals": signals,
        "bull_sigs": bull_sigs,
        "bear_sigs": bear_sigs,
        "price": round(price,2),
        "pct_chg": round(pct_chg,2),
        "ema9": ema9, "ema21": ema21, "ema50": ema50,
        "rsi": rsi_val,
        "atr": round(atr_val,2),
        "vol_ratio": round(vol_ratio,1),
        "recent_high": round(rec_h,2),
        "recent_low": round(rec_l,2),
        "equal_highs": equal_highs,
        "equal_lows": equal_lows,
        "fake_bo_bull": bull_fake_bo,
        "fake_bo_bear": bear_fake_bo,
        "liq_sweep_bull": liq_sweep_bull,
        "liq_sweep_bear": liq_sweep_bear,
        "weekly_trend": "UP" if weekly_trend_up else "DOWN" if weekly_trend_down else "SIDE",
        "trade": trade,
        "mcap_grade": mcap_grade,
        "pos52": pos52,
        "w52h": round(w52h,2),
        "w52l": round(w52l,2),
    }


# ══════════════════════════════════════════════════════════════════════
#  SECTOR STRENGTH — Priyank picks strongest sector first
# ══════════════════════════════════════════════════════════════════════
def rank_sectors(results: list) -> dict:
    from collections import defaultdict
    sector_scores = defaultdict(list)
    for r in results:
        if r.get("analysis"):
            sector_scores[r["sector"]].append(r["analysis"]["score"])
    ranked = {}
    for sec, scores in sector_scores.items():
        ranked[sec] = {
            "avg_score": round(sum(scores)/len(scores), 1),
            "bull_count": sum(1 for s in scores if s >= 15),
            "bear_count": sum(1 for s in scores if s <= -15),
            "count": len(scores),
        }
    return dict(sorted(ranked.items(), key=lambda x: x[1]["avg_score"], reverse=True))


# ══════════════════════════════════════════════════════════════════════
#  PRIYANK PICKS — Best 3 long + 2 short (quality > quantity)
# ══════════════════════════════════════════════════════════════════════
def priyank_picks(results: list, sector_rank: dict) -> dict:
    valid = [r for r in results if r.get("analysis") and r["analysis"]["trade"]]

    def quality_score(r):
        a = r["analysis"]
        t = a["trade"]
        s = a["score"]
        # Priyank weights: Fake BO > Liq Sweep > EMA Cross > RSI Div
        bonus = 0
        if a["fake_bo_bull"] or a["fake_bo_bear"]: bonus += 25  # highest weight
        if a["liq_sweep_bull"] or a["liq_sweep_bear"]: bonus += 20
        if t.get("good_rr"): bonus += 15  # must be >= 1:1.5
        if a["mcap_grade"] == "A": bonus += 10  # liquidity filter
        # Sector bonus — top sector stocks get priority
        sec_rank_pos = list(sector_rank.keys()).index(r["sector"]) if r["sector"] in sector_rank else 99
        sector_bonus = max(0, 20 - sec_rank_pos * 2)
        return abs(s) + bonus + sector_bonus

    # Top LONG picks — different sectors, ordered by quality
    long_candidates = [r for r in valid
                       if r["analysis"]["score"] >= 25
                       and r["analysis"]["trade"]["direction"] == "LONG"
                       and r["analysis"]["trade"].get("good_rr", False)]
    long_candidates.sort(key=quality_score, reverse=True)
    # Ensure different sectors
    seen_sectors = set()
    top_long = []
    for r in long_candidates:
        if r["sector"] not in seen_sectors:
            top_long.append(r)
            seen_sectors.add(r["sector"])
        if len(top_long) >= 3: break

    # Top SHORT picks
    short_candidates = [r for r in valid
                        if r["analysis"]["score"] <= -25
                        and r["analysis"]["trade"]["direction"] == "SHORT"
                        and r["analysis"]["trade"].get("good_rr", False)]
    short_candidates.sort(key=quality_score, reverse=True)
    seen_sectors_s = set()
    top_short = []
    for r in short_candidates:
        if r["sector"] not in seen_sectors_s:
            top_short.append(r)
            seen_sectors_s.add(r["sector"])
        if len(top_short) >= 2: break

    # Watchlist: near setups not yet triggered
    watchlist = [r for r in valid
                 if 10 <= abs(r["analysis"]["score"]) < 25
                 and r["analysis"]["mcap_grade"] in ("A","B")][:5]

    return {"top_long": top_long, "top_short": top_short, "watchlist": watchlist}


# ══════════════════════════════════════════════════════════════════════
#  AI REASONING — OpenRouter picks best and adds narrative
# ══════════════════════════════════════════════════════════════════════
def ai_reasoning(picks: dict, sector_rank: dict, scan_meta: dict) -> str:
    if not OPENROUTER_API_KEY or (not picks["top_long"] and not picks["top_short"]):
        return ""

    def summarize(r):
        a = r["analysis"]; t = a["trade"]
        return (f"{r['sym']} [{r['sector']}] MCap Grade:{a['mcap_grade']}\n"
                f"  Score:{a['score']:+d} | CMP:₹{a['price']} | RSI:{a['rsi']} | Vol:{a['vol_ratio']}x\n"
                f"  Signals: {' | '.join(s['sig'] for s in a['signals'][:4])}\n"
                f"  Entry:₹{t['entry']} SL:₹{t['sl']}(-{t['sl_pct']}%) T1:₹{t['t1']} T2:₹{t['t2']} RR:{t['rr1']}:1\n"
                f"  Timing: {t['timing']}")

    top_sectors = list(sector_rank.items())[:5]
    prompt = f"""You are Priyank Sharma, SEBI-registered research analyst from "HOLD with Priyank" YouTube channel.
You use: Fake Breakouts, Liquidity Sweeps, EMA 9/21, Multi-Timeframe, Fibonacci, min 1:1.5 RR.
Today: {scan_meta.get('scan_time','today')} | Nifty 50 context

TOP SECTORS (by collective momentum):
{chr(10).join(f"{i+1}. {s} — avg score {d['avg_score']:+.0f}, {d['bull_count']} bullish stocks" for i,(s,d) in enumerate(top_sectors))}

TOP LONG SETUPS (math-detected):
{chr(10).join(summarize(r) for r in picks['top_long']) if picks['top_long'] else 'None detected'}

TOP SHORT SETUPS (math-detected):
{chr(10).join(summarize(r) for r in picks['top_short']) if picks['top_short'] else 'None detected'}

Give a sharp 200-word trading brief in Priyank's style:
1. Which sector has smart money TODAY and why
2. For each top pick — why you like it (mention the specific signal: fake BO / liq sweep / EMA cross)
3. Exact entry condition ("enter only if price holds above ₹X")
4. Risk — what invalidates this trade
5. One stock to AVOID today with reason

Be direct, precise, use ₹ prices. Sound like a professional trading coach."""

    print("  🤖 AI generating Priyank-style analysis...")
    return call_ai(prompt, max_tokens=800) or ""


# ══════════════════════════════════════════════════════════════════════
#  SCAN RUNNER
# ══════════════════════════════════════════════════════════════════════
def run_scan(stocks: list, demo=False, verbose=True) -> list:
    results, total = [], len(stocks)
    for idx, stock in enumerate(stocks):
        sym = stock["sym"]
        pct = int((idx+1)/total*100)
        bar = "█"*(pct//5)+"░"*(20-pct//5)
        if verbose:
            print(f"\r  [{bar}] {pct:3d}%  {sym:<14}", end="", flush=True)
        try:
            df = demo_ohlcv(sym) if demo else fetch_ohlcv(stock["yf"])
            analysis = priyank_analyze(df, stock)
            result = {**stock, "analysis": analysis, "error": None}
            if verbose and analysis:
                sigs = [s["sig"] for s in analysis["signals"][:3]]
                fb = " 🪤FAKE-BO" if (analysis["fake_bo_bull"] or analysis["fake_bo_bear"]) else ""
                ls = " 💧SWEEP" if (analysis["liq_sweep_bull"] or analysis["liq_sweep_bear"]) else ""
                dirstr = str(analysis.get('direction') or '----')
                rsistr = str(analysis['rsi'])
                print(f"\r  ✓ {sym:<14} {analysis['score']:+4d}  {dirstr:<6}"
                      f"  RSI:{rsistr:<5} {' '.join(sigs[:2])[:30]}{fb}{ls}", flush=True)
        except Exception as e:
            result = {**stock, "analysis": None, "error": str(e)}
            if verbose: print(f"\r  ✗ {sym:<14} {str(e)[:40]}", flush=True)
        results.append(result)
        if not demo: time.sleep(0.13)
    if verbose: print()
    return results


# ══════════════════════════════════════════════════════════════════════
#  HTML BUILDER — Full Priyank dashboard
# ══════════════════════════════════════════════════════════════════════
def sig_color(t): return "#00e5a0" if t=="BULL" else "#f56060" if t=="BEAR" else "#f5c842"
def weight_color(w): return {"HIGHEST":"#f5c842","HIGH":"#00e5a0","MED":"#2d7ff9","LOW":"#304560"}.get(w,"#304560")

def build_html(results: list, scan_meta: dict, picks: dict, sector_rank: dict, ai_text: str) -> str:
    valid = [r for r in results if r.get("analysis")]
    errors = [r for r in results if r.get("error")]
    bull = sum(1 for r in valid if r["analysis"]["score"] >= 15)
    bear = sum(1 for r in valid if r["analysis"]["score"] <= -15)
    fake_bo_ct = sum(1 for r in valid if r["analysis"].get("fake_bo_bull") or r["analysis"].get("fake_bo_bear"))
    sweep_ct   = sum(1 for r in valid if r["analysis"].get("liq_sweep_bull") or r["analysis"].get("liq_sweep_bear"))
    good_rr_ct = sum(1 for r in valid if r["analysis"].get("trade") and r["analysis"]["trade"].get("good_rr"))
    scan_time  = scan_meta.get("scan_time","—")
    mode_str   = "DEMO" if scan_meta.get("demo") else "LIVE · YAHOO FINANCE"
    ai_mode    = f"AI: {OPENROUTER_MODEL.split('/')[1].split(':')[0]}" if OPENROUTER_API_KEY else "Rule-Based"
    sorted_r   = sorted(valid, key=lambda r: r["analysis"]["score"], reverse=True)
    sectors    = list(sector_rank.keys())

    # ── Pick cards ──
    def pick_card(r, rank_icon, direction):
        a = r["analysis"]; t = a["trade"]
        sc_c = "#00e5a0" if a["score"]>=0 else "#f56060"
        d_c  = "#00e5a0" if direction=="LONG" else "#f56060"
        fb_b = '<span class="mini-b fb-b">🪤 FAKE-BO</span>' if (a["fake_bo_bull"] or a["fake_bo_bear"]) else ""
        ls_b = '<span class="mini-b ls-b">💧 SWEEP</span>' if (a["liq_sweep_bull"] or a["liq_sweep_bear"]) else ""
        gr_b = '<span class="mini-b gr-b">✅ RR≥1.5</span>' if t.get("good_rr") else '<span class="mini-b bad-b">⚠ RR<1.5</span>'
        mcap_b = f'<span class="mini-b {"A-b" if a["mcap_grade"]=="A" else "B-b"}">MCap {a["mcap_grade"]}</span>'
        sigs_html = "".join(
            f'<div class="ps-sig"><span class="ps-sig-dot" style="background:{weight_color(s["weight"])}"></span>'
            f'<span style="color:{sig_color(s["type"])}">{s["sig"]}</span>'
            f'<span class="ps-sig-desc">{s["desc"]}</span></div>'
            for s in a["signals"]
        )
        return f"""
        <div class="pick-card {'' if t.get('good_rr') else 'low-rr'}">
          <div class="pc-top">
            <div>
              <span class="pc-rank">{rank_icon}</span>
              <span class="pc-sym">{r['sym']}</span>
              <span class="pc-sector">{r['sector']}</span>
            </div>
            <div style="text-align:right">
              <span class="pc-score" style="color:{sc_c}">{a['score']:+d}</span>
              <div class="pc-dir" style="color:{d_c};border-color:{d_c}40;background:{d_c}12">{direction}</div>
            </div>
          </div>
          <div class="pc-badges">{fb_b}{ls_b}{gr_b}{mcap_b}</div>
          <div class="pc-cmp">
            CMP ₹{a['price']:,.2f}
            <span style="color:{'#00e5a0' if a['pct_chg']>=0 else '#f56060'}">{a['pct_chg']:+.2f}%</span>
            · RSI {a['rsi']} · Vol {a['vol_ratio']}x
            · Weekly: {a['weekly_trend']}
          </div>
          <div class="pc-levels">
            <div class="pl"><span class="pl-lbl ema-lbl">EMA 9/21/50</span>
              <span class="pl-val" style="color:#9d7cfc">₹{a['ema9']} / ₹{a['ema21']} / ₹{a['ema50']}</span></div>
            <div class="pl"><span class="pl-lbl entry-lbl">ENTRY</span>
              <span class="pl-val" style="color:#2d7ff9">₹{t['entry']:,.2f}</span></div>
            <div class="pl"><span class="pl-lbl sl-lbl">STOP LOSS</span>
              <span class="pl-val" style="color:#f56060">₹{t['sl']:,.2f} <small>(-{t['sl_pct']}%)</small></span></div>
            <div class="pl"><span class="pl-lbl t1-lbl">T1 · Fib 0.618</span>
              <span class="pl-val" style="color:#86efac">₹{t['t1']:,.2f} <small>RR {t['rr1']}:1</small></span></div>
            <div class="pl"><span class="pl-lbl t2-lbl">T2 · Fib 1.272</span>
              <span class="pl-val" style="color:#00e5a0">₹{t['t2']:,.2f} <small>RR {t['rr2']}:1</small></span></div>
            <div class="pl"><span class="pl-lbl t3-lbl">T3 · Fib 1.618</span>
              <span class="pl-val" style="color:#f5c842">₹{t['t3']:,.2f}</span></div>
          </div>
          <div class="pc-timing">⏰ {t['timing']}</div>
          <div class="pc-signals">{sigs_html}</div>
        </div>"""

    longs_html  = "".join(pick_card(r,["🥇","🥈","🥉"][i],  "LONG")  for i,r in enumerate(picks["top_long"]))
    shorts_html = "".join(pick_card(r,["🔻","🔻🔻"][i], "SHORT") for i,r in enumerate(picks["top_short"]))
    no_l = '<div class="no-picks">No high-conviction long setups with RR≥1.5 detected</div>'
    no_s = '<div class="no-picks">No high-conviction short setups detected</div>'

    # Sector bars
    sec_bars = "".join(
        f'<div class="sec-bar"><div class="sb-top"><span>{s}</span>'
        f'<span style="color:{"#00e5a0" if d["avg_score"]>=0 else "#f56060"}">{d["avg_score"]:+.0f}</span></div>'
        f'<div class="sb-track"><div class="sb-fill" style="width:{min(100,max(0,(d["avg_score"]+100)/2))}%;'
        f'background:{"#00e5a0" if d["avg_score"]>=0 else "#f56060"}"></div></div>'
        f'<div class="sb-sub">{d["bull_count"]} bull · {d["bear_count"]} bear</div></div>'
        for s,d in list(sector_rank.items())[:15]
    )
    sec_btns = "".join(f'<button class="fb" onclick="fSec(this,\'{s}\')">{s}</button>' for s in sectors)

    # All rows
    def row_html(r, rank):
        a = r["analysis"]
        t = a.get("trade") or {}
        price = a["price"]
        up = a["pct_chg"] >= 0
        sc_c = "#00e5a0" if a["score"]>=0 else "#f56060"
        cc   = "#00e5a0" if up else "#f56060"
        ri   = ["🥇","🥈","🥉"][rank-1] if rank<=3 else f"#{rank}"
        sent = ("STRONG BULL" if a["score"]>=50 else "BULLISH" if a["score"]>=15
                else "STRONG BEAR" if a["score"]<=-50 else "BEARISH" if a["score"]<=-15 else "NEUTRAL")
        sent_c = ("#00e5a0" if a["score"]>=15 else "#f56060" if a["score"]<=-15 else "#f5c842")
        fb_icon = " 🪤" if a.get("fake_bo_bull") or a.get("fake_bo_bear") else ""
        ls_icon = " 💧" if a.get("liq_sweep_bull") or a.get("liq_sweep_bear") else ""
        sigs_chip = "".join(
            f'<span class="chip" style="color:{sig_color(s["type"])};background:{sig_color(s["type"])}18;'
            f'border:1px solid {sig_color(s["type"])}25">{s["sig"]}</span>'
            for s in a["signals"][:4]
        ) or '<span class="chip" style="color:#304560">NO SIGNAL</span>'

        sig_detail = "".join(
            f'<div class="sr"><span style="color:{weight_color(s["weight"])};font-size:10px">◆</span>'
            f'<span style="color:{sig_color(s["type"])};font-size:10px;font-family:var(--mono)">'
            f'[{s["weight"]}] {s["sig"]} — {s["desc"]}</span></div>'
            for s in a["signals"]
        ) or '<div style="font-family:var(--mono);font-size:10px;color:#304560">No signals</div>'

        trade_html = ""
        if t:
            dc = "#00e5a0" if t["direction"]=="LONG" else "#f56060"
            rr_c = "#00e5a0" if t.get("good_rr") else "#f56060"
            trade_html = f"""
            <div class="tb">
              <div class="tb-hdr">
                <span style="color:{dc};font-weight:600">{t['direction']}</span>
                <span style="color:{rr_c};font-size:10px">RR {t['rr1']}:1 {'✅' if t.get('good_rr') else '⚠ <1.5'}</span>
                <span class="tb-timing">{t['timing']}</span>
              </div>
              <div class="tb-grid">
                <div class="tbc ema-bg"><div class="tbl">EMA 9 / 21 / 50</div>
                  <div class="tbv" style="color:#9d7cfc">₹{a['ema9']} / ₹{a['ema21']} / ₹{a['ema50']}</div></div>
                <div class="tbc"><div class="tbl">RSI · ATR · Vol</div>
                  <div class="tbv" style="color:#f5c842">{a['rsi']} · ₹{a['atr']} · {a['vol_ratio']}x</div></div>
                <div class="tbc entry-bg"><div class="tbl">ENTRY</div>
                  <div class="tbv" style="color:#2d7ff9">₹{t['entry']:,.2f}</div></div>
                <div class="tbc sl-bg"><div class="tbl">STOP LOSS</div>
                  <div class="tbv" style="color:#f56060">₹{t['sl']:,.2f} (-{t['sl_pct']}%)</div></div>
                <div class="tbc"><div class="tbl">T1 · Fib 0.618</div>
                  <div class="tbv" style="color:#86efac">₹{t['t1']:,.2f}</div></div>
                <div class="tbc"><div class="tbl">T2 · Fib 1.272</div>
                  <div class="tbv" style="color:#00e5a0">₹{t['t2']:,.2f}</div></div>
                <div class="tbc"><div class="tbl">T3 · Fib 1.618</div>
                  <div class="tbv" style="color:#f5c842">₹{t['t3']:,.2f}</div></div>
                <div class="tbc"><div class="tbl">Weekly Trend</div>
                  <div class="tbv" style="color:{'#00e5a0' if a['weekly_trend']=='UP' else '#f56060' if a['weekly_trend']=='DOWN' else '#f5c842'}">{a['weekly_trend']}</div></div>
              </div>
              <div style="font-family:var(--mono);font-size:9px;color:#304560;padding:4px 10px">
                52W: ₹{a['w52l']} – ₹{a['w52h']} · Position: {a['pos52']}% · 
                EqHighs: {a['equal_highs']} · EqLows: {a['equal_lows']}
              </div>
            </div>"""

        return f"""
        <div class="row" data-score="{a['score']}" data-sector="{r['sector']}"
             data-sent="{'BULL' if a['score']>=15 else 'BEAR' if a['score']<=-15 else 'NEUTRAL'}"
             data-fb="{'1' if a.get('fake_bo_bull') or a.get('fake_bo_bear') else '0'}"
             data-sweep="{'1' if a.get('liq_sweep_bull') or a.get('liq_sweep_bear') else '0'}"
             data-goodrr="{'1' if t.get('good_rr') else '0'}"
             data-mcap="{a['mcap_grade']}">
          <div class="rm" onclick="tog('{r['sym']}_{rank}')">
            <div class="rnk">{ri}</div>
            <div>
              <div class="sym">{r['sym']}<span style="font-size:9px">{fb_icon}{ls_icon}</span></div>
              <div class="stag">{r['sector']} · {a['mcap_grade']}</div>
            </div>
            <div class="score" style="color:{sc_c}">{a['score']:+d}</div>
            <div class="cchips">{sigs_chip}</div>
            <div class="cprice">
              <div class="price">₹{price:,.1f}</div>
              <div style="font-family:var(--mono);font-size:9px;color:{cc}">{'+' if up else ''}{a['pct_chg']}%</div>
            </div>
            <div class="sent" style="color:{sent_c};background:{sent_c}18;border:1px solid {sent_c}30">{sent}</div>
            <div style="font-family:var(--mono);font-size:9px;text-align:right;color:#304560">
              {t.get('direction','—')}<br>SL ₹{t.get('sl','—')}
            </div>
            <div class="ei" id="ei-{r['sym']}_{rank}">▼</div>
          </div>
          <div class="rd" id="det-{r['sym']}_{rank}" style="display:none">
            <div class="d3c">
              <div><div class="dt">PRIYANK SIGNALS ({len(a['signals'])})</div>{sig_detail}</div>
              <div>{trade_html}</div>
              <div></div>
            </div>
          </div>
        </div>"""

    rows_html = "".join(row_html(r,i+1) for i,r in enumerate(sorted_r))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Priyank Scanner — Nifty 500 — {scan_time}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --bg:#04060c;--s1:#080c18;--s2:#0b1020;--b1:#131d2e;--b2:#1a2840;
  --tx:#c8daf5;--mu:#304560;--g:#00e5a0;--b:#2d7ff9;--y:#f5c842;--r:#f56060;--p:#9d7cfc;
  --mono:'JetBrains Mono',monospace;--dis:'Orbitron',monospace;--body:'Rajdhani',sans-serif;
}}
body{{background:var(--bg);font-family:var(--body);color:var(--tx);min-height:100vh;}}
body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,229,160,.005) 3px,rgba(0,229,160,.005) 4px);}}
.w{{max-width:1300px;margin:0 auto;padding:14px 12px 60px;position:relative;z-index:1;}}

/* HEADER */
.hdr{{text-align:center;padding:22px 0 16px;border-bottom:1px solid var(--b1);margin-bottom:16px;
  background:radial-gradient(ellipse 70% 100% at 50% 0%,rgba(45,127,249,.06) 0%,transparent 70%);}}
.hdr-b{{font-family:var(--mono);font-size:9px;letter-spacing:.2em;color:var(--g);
  border:1px solid rgba(0,229,160,.2);padding:3px 12px;border-radius:20px;
  display:inline-flex;align-items:center;gap:5px;margin-bottom:9px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--g);}}
h1{{font-family:var(--dis);font-size:clamp(14px,3.5vw,32px);font-weight:900;letter-spacing:.1em;
  background:linear-gradient(90deg,#fff 0%,#f5c842 30%,#00e5a0 65%,#9d7cfc 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.hdr-sub{{font-family:var(--mono);font-size:9px;color:var(--mu);letter-spacing:.07em;margin-top:5px;line-height:1.8;}}
.meta-row{{display:flex;justify-content:center;gap:10px;margin-top:10px;flex-wrap:wrap;}}
.meta{{font-family:var(--mono);font-size:9px;color:var(--mu);padding:3px 10px;
  border:1px solid var(--b2);border-radius:4px;}}
.meta span{{color:var(--g);font-weight:600;}}

/* METHODOLOGY BOX */
.meth{{background:var(--s1);border:1px solid rgba(245,200,66,.2);border-radius:10px;
  padding:13px 16px;margin-bottom:16px;}}
.meth-title{{font-family:var(--mono);font-size:9px;color:var(--y);text-transform:uppercase;
  letter-spacing:.16em;margin-bottom:10px;display:flex;align-items:center;gap:7px;}}
.meth-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;}}
.meth-item{{display:flex;gap:8px;align-items:flex-start;}}
.meth-num{{width:22px;height:22px;border-radius:50%;background:rgba(245,200,66,.15);
  color:var(--y);font-family:var(--mono);font-size:9px;font-weight:700;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.meth-txt{{font-size:11px;line-height:1.5;}}
.meth-txt strong{{color:var(--tx);display:block;}}
.meth-txt span{{color:var(--mu);}}

/* AI ANALYSIS BOX */
.ai-box{{background:var(--s1);border:1px solid rgba(157,124,252,.25);border-radius:10px;
  padding:13px 16px;margin-bottom:16px;}}
.ai-title{{font-family:var(--mono);font-size:9px;color:var(--p);text-transform:uppercase;
  letter-spacing:.16em;margin-bottom:8px;display:flex;align-items:center;gap:7px;}}
.ai-text{{font-family:var(--mono);font-size:11.5px;color:#8090b0;line-height:1.85;white-space:pre-wrap;}}
.ai-placeholder{{font-family:var(--mono);font-size:10px;color:#304560;padding:8px;
  border:1px dashed var(--b2);border-radius:6px;}}

/* STATS */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(95px,1fr));gap:6px;margin-bottom:14px;}}
.stat{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;padding:9px 11px;text-align:center;}}
.stl{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.14em;margin-bottom:3px;}}
.stv{{font-family:var(--dis);font-size:20px;font-weight:700;}}

/* PICKS */
.picks{{margin-bottom:20px;}}
.picks-title{{font-family:var(--dis);font-size:clamp(13px,2.5vw,22px);letter-spacing:.1em;text-align:center;
  background:linear-gradient(90deg,#f5c842,#00e5a0);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text;margin-bottom:4px;}}
.picks-sub{{font-family:var(--mono);font-size:9px;color:var(--mu);text-align:center;
  -webkit-text-fill-color:var(--mu);margin-bottom:14px;display:block;}}
.picks-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;}}
.col-hdr{{font-family:var(--dis);font-size:11px;letter-spacing:.1em;padding:8px 14px;
  border-radius:7px;text-align:center;margin-bottom:8px;}}
.bull-h{{background:rgba(0,229,160,.1);color:var(--g);border:1px solid rgba(0,229,160,.2);}}
.bear-h{{background:rgba(245,96,96,.1);color:var(--r);border:1px solid rgba(245,96,96,.2);}}
.watch-h{{background:rgba(245,200,66,.08);color:var(--y);border:1px solid rgba(245,200,66,.18);}}
.pick-card{{background:var(--s1);border:1px solid var(--b2);border-radius:10px;padding:13px;margin-bottom:8px;}}
.pick-card.low-rr{{border-color:rgba(245,96,96,.2);}}
.pc-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:7px;}}
.pc-rank{{font-size:18px;margin-right:6px;}}
.pc-sym{{font-family:var(--dis);font-size:16px;font-weight:900;color:#fff;letter-spacing:.05em;}}
.pc-sector{{font-family:var(--mono);font-size:8px;color:var(--mu);display:block;margin-top:2px;}}
.pc-score{{font-family:var(--dis);font-size:20px;font-weight:900;}}
.pc-dir{{font-family:var(--mono);font-size:9px;padding:2px 9px;border-radius:4px;border:1px solid;text-align:center;margin-top:3px;letter-spacing:.08em;}}
.pc-badges{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px;}}
.mini-b{{font-family:var(--mono);font-size:9px;padding:2px 7px;border-radius:4px;}}
.fb-b{{background:rgba(245,200,66,.12);color:var(--y);border:1px solid rgba(245,200,66,.25);}}
.ls-b{{background:rgba(45,127,249,.12);color:var(--b);border:1px solid rgba(45,127,249,.25);}}
.gr-b{{background:rgba(0,229,160,.1);color:var(--g);border:1px solid rgba(0,229,160,.2);}}
.bad-b{{background:rgba(245,96,96,.1);color:var(--r);border:1px solid rgba(245,96,96,.2);}}
.A-b{{background:rgba(157,124,252,.12);color:var(--p);border:1px solid rgba(157,124,252,.25);}}
.B-b{{background:rgba(245,200,66,.08);color:var(--y);border:1px solid rgba(245,200,66,.18);}}
.pc-cmp{{font-family:var(--mono);font-size:11px;color:var(--tx);margin-bottom:8px;}}
.pc-levels{{display:flex;flex-direction:column;gap:4px;margin-bottom:7px;}}
.pl{{display:grid;grid-template-columns:110px 1fr;gap:5px;align-items:baseline;}}
.pl-lbl{{font-family:var(--mono);font-size:8px;text-transform:uppercase;letter-spacing:.09em;color:var(--mu);}}
.pl-val{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.ema-lbl{{color:var(--p)!important;}} .entry-lbl{{color:var(--b)!important;}}
.sl-lbl{{color:var(--r)!important;}} .t1-lbl{{color:#86efac!important;}}
.t2-lbl{{color:var(--g)!important;}} .t3-lbl{{color:var(--y)!important;}}
.pc-timing{{font-family:var(--mono);font-size:10px;color:var(--y);margin-bottom:8px;padding:5px 7px;
  background:rgba(245,200,66,.05);border-radius:5px;border-left:2px solid rgba(245,200,66,.3);}}
.pc-signals{{display:flex;flex-direction:column;gap:4px;}}
.ps-sig{{display:flex;gap:6px;align-items:flex-start;}}
.ps-sig-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:2px;}}
.ps-sig-desc{{font-family:var(--mono);font-size:9px;color:var(--mu);margin-left:4px;}}
.no-picks{{font-family:var(--mono);font-size:11px;color:var(--mu);
  text-align:center;padding:20px;border:1px dashed var(--b2);border-radius:8px;}}

/* SECTOR */
.sec-s{{background:var(--s1);border:1px solid var(--b1);border-radius:9px;padding:12px 14px;margin-bottom:14px;}}
.sec-t{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.16em;margin-bottom:10px;}}
.sec-bars{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:7px;}}
.sec-bar{{display:flex;flex-direction:column;gap:2px;}}
.sb-top{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;}}
.sb-track{{height:4px;background:var(--b2);border-radius:2px;overflow:hidden;}}
.sb-fill{{height:100%;border-radius:2px;}}
.sb-sub{{font-family:var(--mono);font-size:8px;color:var(--mu);}}

/* CONTROLS */
.ctrl{{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-bottom:7px;}}
.ctrl-lbl{{font-family:var(--mono);font-size:8px;color:var(--mu);letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;}}
.fb{{padding:5px 10px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);
  color:var(--mu);font-family:var(--mono);font-size:9px;cursor:pointer;transition:all .12s;text-transform:uppercase;white-space:nowrap;}}
.fb:hover,.fb.on{{border-color:var(--b);color:var(--b);background:rgba(45,127,249,.07);}}
.fb.on-fb{{border-color:var(--y)!important;color:var(--y)!important;background:rgba(245,200,66,.08)!important;}}
.fb.on-sw{{border-color:var(--b)!important;color:var(--b)!important;background:rgba(45,127,249,.1)!important;}}
.si{{padding:6px 12px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);
  color:var(--tx);font-family:var(--mono);font-size:11px;outline:none;min-width:130px;}}
.si:focus{{border-color:var(--b);}}
.si::placeholder{{color:var(--mu);}}

/* TABLE */
.th{{display:grid;grid-template-columns:32px 115px 60px 1fr 90px 110px 88px 20px;
  gap:5px;padding:6px 10px;font-family:var(--mono);font-size:7px;text-transform:uppercase;
  letter-spacing:.12em;color:var(--mu);border-bottom:1px solid var(--b1);margin-bottom:3px;}}
.results{{display:flex;flex-direction:column;gap:4px;}}
.row{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;overflow:hidden;}}
.rm{{display:grid;grid-template-columns:32px 115px 60px 1fr 90px 110px 88px 20px;
  gap:5px;padding:8px 10px;align-items:center;cursor:pointer;transition:background .12s;}}
.rm:hover{{background:var(--s2);}}
.rnk{{font-family:var(--dis);font-size:10px;color:var(--mu);text-align:center;}}
.sym{{font-family:var(--dis);font-size:13px;font-weight:700;color:#fff;letter-spacing:.04em;}}
.stag{{font-family:var(--mono);font-size:8px;color:var(--mu);margin-top:1px;}}
.score{{font-family:var(--dis);font-size:16px;font-weight:900;}}
.cchips{{display:flex;flex-wrap:wrap;gap:2px;}}
.chip{{font-family:var(--mono);font-size:8px;padding:2px 5px;border-radius:3px;font-weight:600;white-space:nowrap;}}
.cprice{{text-align:right;}}
.price{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.sent{{padding:4px 7px;border-radius:5px;font-family:var(--dis);font-size:8px;font-weight:700;text-align:center;white-space:nowrap;}}
.ei{{color:var(--mu);font-size:9px;text-align:center;transition:transform .17s;}}
.rd{{border-top:1px solid var(--b1);padding:12px 10px;background:rgba(4,6,12,.65);}}
.d3c{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:11px;}}
@media(max-width:900px){{.d3c,.th,.rm{{grid-template-columns:1fr;}}}}
.dt{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.12em;margin-bottom:7px;}}
.sr{{display:flex;gap:6px;align-items:flex-start;margin-bottom:5px;}}
.tb{{background:rgba(8,12,24,.8);border:1px solid var(--b2);border-radius:7px;overflow:hidden;}}
.tb-hdr{{padding:7px 11px;border-bottom:1px solid var(--b1);display:flex;align-items:center;
  gap:8px;font-family:var(--mono);font-size:10px;flex-wrap:wrap;}}
.tb-timing{{font-family:var(--mono);font-size:9px;color:var(--y);flex:1;}}
.tb-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;padding:8px 10px;}}
.tbc{{background:var(--s2);border:1px solid var(--b1);border-radius:4px;padding:6px 8px;}}
.tbc.ema-bg{{border-color:rgba(157,124,252,.2);}} .tbc.entry-bg{{border-color:rgba(45,127,249,.2);}} .tbc.sl-bg{{border-color:rgba(245,96,96,.2);}}
.tbl{{font-family:var(--mono);font-size:7px;color:var(--mu);text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px;}}
.tbv{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.err{{font-family:var(--mono);font-size:9px;color:#304560;padding:6px 10px;margin-top:5px;}}
.dis{{text-align:center;font-family:var(--mono);font-size:8px;color:#0d1820;margin-top:28px;line-height:2;}}
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-track{{background:var(--b1);}}
::-webkit-scrollbar-thumb{{background:var(--b2);border-radius:2px;}}
</style>
</head>
<body>
<div class="w">

<div class="hdr">
  <div class="hdr-b"><span class="dot"></span>PRIYANK SHARMA METHODOLOGY · NIFTY 500 · "HOLD WITH PRIYANK"</div>
  <h1>PRIYANK SCANNER — NIFTY 500</h1>
  <div class="hdr-sub">
    Fake Breakout · Liquidity Sweep · EMA 9/21 · Multi-Timeframe · Fibonacci 1.272/1.618 · Min RR 1:1.5 · MCap Filter
  </div>
  <div class="meta-row">
    <div class="meta">SCANNED <span>{len(valid)}</span></div>
    <div class="meta">BULL SETUPS <span>{bull}</span></div>
    <div class="meta">BEAR SETUPS <span>{bear}</span></div>
    <div class="meta">FAKE BO <span>{fake_bo_ct}</span></div>
    <div class="meta">LIQ SWEEP <span>{sweep_ct}</span></div>
    <div class="meta">RR≥1.5 <span>{good_rr_ct}</span></div>
    <div class="meta">PICKS ENGINE <span>{ai_mode}</span></div>
    <div class="meta">SCAN <span>{scan_time}</span></div>
  </div>
</div>

<!-- METHODOLOGY -->
<div class="meth">
  <div class="meth-title">📖 PRIYANK SHARMA METHODOLOGY — How This Scanner Works</div>
  <div class="meth-grid">
    <div class="meth-item"><div class="meth-num">1</div><div class="meth-txt">
      <strong>MCap Filter (Liquidity)</strong>
      <span>Grade A = ₹1L+ Cr · Grade B = ₹30k Cr · Only institutional stocks. Low liquidity = skip.</span></div></div>
    <div class="meth-item"><div class="meth-num">2</div><div class="meth-txt">
      <strong>Sector Strength First</strong>
      <span>Finds which sector smart money is rotating into. Picks best stocks from strongest sectors.</span></div></div>
    <div class="meth-item"><div class="meth-num">3</div><div class="meth-txt">
      <strong>Fake Breakout 🪤 (Highest Weight)</strong>
      <span>Price breaks key level → traps retail → reverses with volume. Priyank's signature setup.</span></div></div>
    <div class="meth-item"><div class="meth-num">4</div><div class="meth-txt">
      <strong>Liquidity Sweep 💧 (High Weight)</strong>
      <span>Equal highs/lows = stop-loss clusters. Smart money hunts stops then reverses.</span></div></div>
    <div class="meth-item"><div class="meth-num">5</div><div class="meth-txt">
      <strong>EMA 9/21 Setup (High Weight)</strong>
      <span>Fresh EMA9 × EMA21 crossover = trend entry. Price above EMA21 = uptrend. Execute on 5m/15m.</span></div></div>
    <div class="meth-item"><div class="meth-num">6</div><div class="meth-txt">
      <strong>Multi-Timeframe (MTF)</strong>
      <span>Weekly trend confirms daily setup. Only take longs in weekly uptrend. Bears in downtrend.</span></div></div>
    <div class="meth-item"><div class="meth-num">7</div><div class="meth-txt">
      <strong>Fibonacci Targets</strong>
      <span>T1 = Fib 0.618 ext · T2 = 1.272 (Priyank's preferred exit) · T3 = 1.618 (trail SL)</span></div></div>
    <div class="meth-item"><div class="meth-num">8</div><div class="meth-txt">
      <strong>Risk-Reward ≥ 1:1.5</strong>
      <span>Minimum 1:1.5 RR. Ideal 1:2. If RR < 1.5, skip the trade. Quality over quantity.</span></div></div>
  </div>
</div>

<!-- AI ANALYSIS -->
<div class="ai-box">
  <div class="ai-title">🤖 PRIYANK-STYLE AI TRADE BRIEF ({ai_mode})</div>
  {f'<div class="ai-text">{ai_text}</div>' if ai_text else
   f'<div class="ai-placeholder">Set OPENROUTER_API_KEY to get Priyank-style AI analysis.<br>Free key at openrouter.ai → Use model: deepseek/deepseek-r1:free</div>'}
</div>

<!-- STATS -->
<div class="stats">
  {''.join(f'<div class="stat"><div class="stl">{l}</div><div class="stv" style="color:{c}">{v}</div></div>' for l,v,c in [
    ("Scanned",len(valid),"var(--b)"),("Bull Setups",bull,"var(--g)"),("Bear Setups",bear,"var(--r)"),
    ("Fake BO",fake_bo_ct,"var(--y)"),("Liq Sweep",sweep_ct,"var(--b)"),
    ("RR≥1.5",good_rr_ct,"var(--g)"),("Mode",mode_str,"var(--mu)")])}
</div>

<!-- PICKS -->
<div class="picks">
  <div class="picks-title">📅 TODAY'S HIGH-CONVICTION PICKS</div>
  <div class="picks-sub">Priyank's "Less is More" — Max 3 Long · 2 Short · Different sectors · All with RR≥1.5</div>
  <div class="picks-grid">
    <div>
      <div class="col-hdr bull-h">🟢 BEST LONG SETUPS ({len(picks['top_long'])})</div>
      {longs_html or no_l}
    </div>
    <div>
      <div class="col-hdr bear-h">🔴 BEST SHORT SETUPS ({len(picks['top_short'])})</div>
      {shorts_html or no_s}
    </div>
    <div>
      <div class="col-hdr watch-h">👁 WATCHLIST — Near Setup ({len(picks['watchlist'])})</div>
      {''.join(f'<div class="pick-card" style="opacity:.8"><div class="pc-top"><div><span class="pc-sym">{r["sym"]}</span><span class="pc-sector">{r["sector"]}</span></div><span class="pc-score" style="color:#f5c842">{r["analysis"]["score"]:+d}</span></div><div class="pc-cmp">CMP ₹{r["analysis"]["price"]:,.2f} · RSI {r["analysis"]["rsi"]} · {", ".join(s["sig"] for s in r["analysis"]["signals"][:2])}</div><div class="pc-timing">⏳ Setup forming — wait for confirmation</div></div>' for r in picks["watchlist"]) or no_l}
    </div>
  </div>
</div>

<!-- SECTOR STRENGTH -->
<div class="sec-s">
  <div class="sec-t">⚡ SECTOR STRENGTH RANKING (Priyank: trade strongest sector stocks)</div>
  <div class="sec-bars">{sec_bars}</div>
</div>

<!-- CONTROLS -->
<div class="ctrl">
  <span class="ctrl-lbl">Filter:</span>
  <button class="fb on" onclick="fSent(this,'ALL')">ALL</button>
  <button class="fb" onclick="fSent(this,'BULL')">BULL</button>
  <button class="fb" onclick="fSent(this,'BEAR')">BEAR</button>
  <button class="fb" onclick="fFB(this)">🪤 FAKE-BO</button>
  <button class="fb" onclick="fSW(this)">💧 SWEEP</button>
  <button class="fb" onclick="fRR(this)">✅ RR≥1.5</button>
  <button class="fb" onclick="fMcap(this,'A')">MCap A</button>
  <input class="si" placeholder="Search symbol…" oninput="fSearch(this.value)">
  <span class="ctrl-lbl" style="margin-left:auto">Sort:</span>
  <button class="fb on" onclick="srt('score')">Score</button>
  <button class="fb" onclick="srt('rsi')">RSI</button>
</div>
<div class="ctrl" style="margin-bottom:12px;gap:4px">
  <span class="ctrl-lbl">Sector:</span>
  <button class="fb on" onclick="fSec(this,'ALL')">ALL</button>
  {sec_btns}
</div>

<div class="th"><div>#</div><div>STOCK</div><div>SCORE</div><div>PRIYANK SIGNALS</div>
  <div>PRICE</div><div>SENTIMENT</div><div>DIR / SL</div><div></div></div>
<div class="results" id="rc">{rows_html}</div>
{f'<div class="err">⚠ {len(errors)} errors: {", ".join(r["sym"] for r in errors[:8])}</div>' if errors else ""}

<div class="dis">
  PRIYANK SHARMA METHODOLOGY · {len(valid)} NIFTY 500 STOCKS · DATA: {mode_str}<br>
  FOR EDUCATIONAL PURPOSES ONLY · NOT SEBI REGISTERED ADVICE · ALWAYS VERIFY BEFORE TRADING
</div>
</div>

<script>
let F={{sent:'ALL',sec:'ALL',search:'',fb:false,sw:false,rr:false,mcap:''}};
function apF(){{
  const rows=[...document.querySelectorAll('.row')];let vis=[];
  rows.forEach(r=>{{
    const s=r.dataset.sent,sec=r.dataset.sector,sc=parseInt(r.dataset.score);
    const fb=r.dataset.fb,sw=r.dataset.sweep,gr=r.dataset.goodrr,mc=r.dataset.mcap;
    const sym=r.querySelector('.sym').textContent.toLowerCase();
    let show=true;
    if(F.fb&&fb!=='1') show=false;
    else if(F.sw&&sw!=='1') show=false;
    else if(F.rr&&gr!=='1') show=false;
    else if(F.mcap&&mc!==F.mcap) show=false;
    else if(!F.fb&&!F.sw&&!F.rr&&F.sent!=='ALL'&&s!==F.sent) show=false;
    if(F.sec!=='ALL'&&sec!==F.sec) show=false;
    if(F.search&&!sym.includes(F.search.toLowerCase())) show=false;
    r.style.display=show?'':'none';if(show) vis.push(r);
  }});
  const rc=document.getElementById('rc');
  vis.sort((a,b)=>parseInt(b.dataset.score)-parseInt(a.dataset.score));
  vis.forEach(r=>rc.appendChild(r));
}}
function clr(){{document.querySelectorAll('.ctrl .fb').forEach(b=>b.classList.remove('on','on-fb','on-sw'));}}
function fSent(btn,v){{clr();btn.classList.add('on');F.sent=v;F.fb=F.sw=F.rr=false;F.mcap='';apF();}}
function fFB(btn){{clr();btn.classList.add('on','on-fb');F.fb=true;F.sw=F.rr=false;apF();}}
function fSW(btn){{clr();btn.classList.add('on','on-sw');F.sw=true;F.fb=F.rr=false;apF();}}
function fRR(btn){{clr();btn.classList.add('on');F.rr=true;F.fb=F.sw=false;apF();}}
function fMcap(btn,v){{clr();btn.classList.add('on');F.mcap=v;F.fb=F.sw=F.rr=false;apF();}}
function fSec(btn,v){{document.querySelectorAll('.ctrl:nth-of-type(2) .fb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');F.sec=v;apF();}}
function fSearch(v){{F.search=v;apF();}}
function srt(v){{apF();}}
function tog(id){{
  const d=document.getElementById('det-'+id),e=document.getElementById('ei-'+id);
  if(d.style.display==='none'){{d.style.display='block';e.style.transform='rotate(180deg)';}}
  else{{d.style.display='none';e.style.transform='';}}
}}
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════
#  CLI MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="Priyank Sharma Scanner — Nifty 500")
    ap.add_argument("--top",    type=int,  default=None, help="Top N stocks by MCap")
    ap.add_argument("--sector", type=str,  default=None, help="Specific sector")
    ap.add_argument("--sym",    type=str,  default=None, help="Specific symbols CSV")
    ap.add_argument("--demo",   action="store_true",     help="Demo mode (no internet)")
    ap.add_argument("--serve",  action="store_true",     help="Flask web server")
    ap.add_argument("--port",   type=int,  default=5000)
    ap.add_argument("--output", type=str,  default=None)
    ap.add_argument("--no-ai",  action="store_true",     help="Skip AI reasoning")
    args = ap.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  PRIYANK SHARMA SCANNER — NIFTY 500                                 ║
║  Fake Breakout · Liquidity Sweep · EMA 9/21 · Fib · RR≥1.5        ║
╚══════════════════════════════════════════════════════════════════════╝""")

    if OPENROUTER_API_KEY and not args.no_ai:
        print(f"  🤖 AI: {OPENROUTER_MODEL}")
    else:
        print("  📐 Rule-Based Mode | Set OPENROUTER_API_KEY for AI (free at openrouter.ai)")

    if args.sym:
        syms = [s.strip().upper() for s in args.sym.split(",")]
        stocks = [s for s in NIFTY500 if s["sym"] in syms]
    elif args.sector:
        stocks = [s for s in NIFTY500 if s["sector"].lower() == args.sector.lower()]
    elif args.top:
        stocks = sorted(NIFTY500, key=lambda s: s["mcap"], reverse=True)[:args.top]
    else:
        stocks = NIFTY500.copy()

    if not YF_AVAILABLE and not args.demo:
        print("  ⚠  yfinance not found — demo mode"); args.demo = True

    print(f"  Stocks: {len(stocks)} | Mode: {'DEMO' if args.demo else 'LIVE'}\n")
    t0 = time.time()
    results = run_scan(stocks, demo=args.demo)
    elapsed = round(time.time()-t0, 1)

    valid = [r for r in results if r.get("analysis")]
    sector_rank = rank_sectors(results)
    picks = priyank_picks(results, sector_rank)

    print(f"\n  ✅ {elapsed}s · {len(valid)} stocks\n")
    print(f"  ── TOP SECTORS ─────────────────────────────")
    for i,(sec,d) in enumerate(list(sector_rank.items())[:5]):
        print(f"  {i+1}. {sec:<14} avg {d['avg_score']:+.0f}  {d['bull_count']} bull / {d['bear_count']} bear")

    print(f"\n  ── TOP LONG PICKS (Priyank Quality Picks) ──")
    for r in picks["top_long"]:
        a=r["analysis"]; t=a["trade"]
        fb=" 🪤FAKE-BO" if a.get("fake_bo_bull") else ""
        ls=" 💧SWEEP" if a.get("liq_sweep_bull") else ""
        print(f"  {r['sym']:<14} {a['score']:+4d}  E:₹{t['entry']}  SL:₹{t['sl']}  "
              f"T2:₹{t['t2']}  RR:{t['rr1']}:1{fb}{ls}")

    print(f"\n  ── TOP SHORT PICKS ──────────────────────────")
    for r in picks["top_short"]:
        a=r["analysis"]; t=a["trade"]
        print(f"  {r['sym']:<14} {a['score']:+4d}  E:₹{t['entry']}  SL:₹{t['sl']}  T2:₹{t['t2']}  RR:{t['rr1']}:1")

    ai_text = ""
    if OPENROUTER_API_KEY and not args.no_ai:
        ai_text = ai_reasoning(picks, sector_rank, {"scan_time": datetime.now().strftime("%d %b %Y, %I:%M %p")})

    meta = {"scan_time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "demo": args.demo, "elapsed": elapsed}
    out = args.output or f"priyank_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    Path(out).write_text(build_html(results, meta, picks, sector_rank, ai_text), encoding="utf-8")
    print(f"\n  💾 Report: {out}")

    if args.serve:
        try:
            from flask import Flask, Response
            app = Flask(__name__)
            @app.route("/")
            def index():
                r2 = run_scan(stocks, demo=args.demo, verbose=False)
                sr2 = rank_sectors(r2)
                p2 = priyank_picks(r2, sr2)
                ai2 = ai_reasoning(p2,sr2,meta) if OPENROUTER_API_KEY and not args.no_ai else ""
                return Response(build_html(r2,meta,p2,sr2,ai2), mimetype="text/html")
            print(f"\n  🌐 http://localhost:{args.port}")
            webbrowser.open(f"http://localhost:{args.port}")
            app.run(host="0.0.0.0", port=args.port, debug=False)
        except ImportError:
            print("  pip install flask")
    else:
        webbrowser.open(f"file://{Path(out).resolve()}")

if __name__ == "__main__":
    main()
