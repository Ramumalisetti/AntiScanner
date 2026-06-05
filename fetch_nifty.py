import pandas as pd
import requests
import json
import traceback

try:
    print("Fetching Nifty 500 list from NSE...")
    url = 'https://archives.nseindia.com/content/indices/ind_nifty500list.csv'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    res = requests.get(url, headers=headers, timeout=10)
    
    with open('nifty500.csv', 'wb') as f:
        f.write(res.content)

    df = pd.read_csv('nifty500.csv')
    universe = []
    for index, row in df.iterrows():
        sym = str(row['Symbol']).strip()
        sector = str(row.get('Industry', 'Unknown')).strip()
        universe.append({'sym': sym, 'yf': f'{sym}.NS', 'sector': sector})

    print(f'Found {len(universe)} stocks.')
    
    # Read api.py and replace UNIVERSE
    with open('api.py', 'r', encoding='utf-8') as f:
        api_code = f.read()
        
    # Find where UNIVERSE is defined
    start_idx = api_code.find('UNIVERSE = [')
    end_idx = api_code.find(']', start_idx) + 1
    
    if start_idx != -1 and end_idx != -1:
        # Generate the new UNIVERSE code string
        new_universe_code = 'UNIVERSE = [\n'
        for u in universe:
            new_universe_code += f'    {{"sym":"{u["sym"]}","yf":"{u["yf"]}","sector":"{u["sector"]}"}},\n'
        new_universe_code += ']'
        
        # Replace in api.py
        new_api_code = api_code[:start_idx] + new_universe_code + api_code[end_idx:]
        
        with open('api.py', 'w', encoding='utf-8') as f:
            f.write(new_api_code)
            
        print("Successfully updated api.py with all 500 stocks!")
    else:
        print("Could not find UNIVERSE definition in api.py")
        
except Exception as e:
    print("Error:", e)
    traceback.print_exc()
