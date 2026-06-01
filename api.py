import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import existing scanners
import darvax_scanner
import priyank_scanner

app = Flask(__name__)
CORS(app)  # Allow React frontend to access

def scan_stock_darvas(stock):
    try:
        df = darvax_scanner.fetch_ohlcv(stock["yf"])
        a = darvax_scanner.analyze(df, stock)
        return {**stock, "a": a, "error": None}
    except Exception as e:
        return {**stock, "a": None, "error": str(e)}

def scan_stock_priyank(stock):
    try:
        df = priyank_scanner.fetch_ohlcv(stock["yf"], days=90)
        a = priyank_scanner.priyank_analyze(df, stock)
        return {**stock, "analysis": a, "error": None}
    except Exception as e:
        return {**stock, "analysis": None, "error": str(e)}

@app.route('/api/scan/darvas', methods=['GET'])
def run_darvas_scan():
    # Allow limiting for faster testing
    limit = int(request.args.get('limit', 0))
    universe = darvax_scanner.UNIVERSE
    if limit > 0:
        universe = universe[:limit]
        
    start_time = time.time()
    results = []
    
    # Use ThreadPool to speed up Yahoo Finance downloads
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scan_stock_darvas, stock): stock for stock in universe}
        for future in as_completed(futures):
            res = future.result()
            if res.get("a"): # Only keep successful analyses
                results.append(res)
                
    # Rank and pick
    sr = darvax_scanner.sector_rank(results)
    pk = darvax_scanner.picks(results, sr)
    
    elapsed = round(time.time() - start_time, 2)
    return jsonify({
        "status": "success",
        "time_taken": elapsed,
        "scanned_count": len(universe),
        "data": pk
    })

@app.route('/api/scan/smc', methods=['GET'])
def run_priyank_scan():
    limit = int(request.args.get('limit', 0))
    universe = priyank_scanner.NIFTY500
    if limit > 0:
        universe = universe[:limit]
        
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scan_stock_priyank, stock): stock for stock in universe}
        for future in as_completed(futures):
            res = future.result()
            if res.get("analysis"):
                results.append(res)
                
    sr = priyank_scanner.rank_sectors(results)
    pk = priyank_scanner.priyank_picks(results, sr)
    
    elapsed = round(time.time() - start_time, 2)
    return jsonify({
        "status": "success",
        "time_taken": elapsed,
        "scanned_count": len(universe),
        "data": pk
    })

if __name__ == '__main__':
    print("Starting Elite Scanner API on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
