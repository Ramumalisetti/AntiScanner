import pandas as pd
import requests
import json

print("Fetching Nifty 500 list from NSE...")
url = 'https://archives.nseindia.com/content/indices/ind_nifty500list.csv'
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers, timeout=10)

with open('nifty500.csv', 'wb') as f:
    f.write(res.content)

df = pd.read_csv('nifty500.csv')
universe = []
for index, row in df.iterrows():
    sym = str(row['Symbol']).strip()
    sector = str(row.get('Industry', 'Unknown')).strip()
    universe.append({'sym': sym, 'yf': f'{sym}.NS', 'sector': sector})

with open('universe.json', 'w') as f:
    json.dump(universe, f, indent=4)

print(f"Saved {len(universe)} stocks to universe.json")
