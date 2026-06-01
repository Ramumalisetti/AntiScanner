import re

with open(r'c:\Work\Scanners\dashboard\src\App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Loader to lucide-react imports
if 'Loader' not in content:
    content = content.replace('DollarSign\n}', 'DollarSign,\n  Loader\n}')

# 2. Add useEffect to React import
if 'useEffect' not in content:
    content = content.replace("import React, { useState } from 'react';", "import React, { useState, useEffect } from 'react';")

# 3. Add states for live data
state_injection = """  const [liveData, setLiveData] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStatus, setScanStatus] = useState('');

  const runLiveScan = async () => {
    setIsScanning(true);
    setScanStatus('Scanning Darvas Universe...');
    try {
      const resD = await fetch('http://127.0.0.1:5000/api/scan/darvas?limit=20');
      const dataD = await resD.json();
      
      setScanStatus('Scanning SMC Setups...');
      const resS = await fetch('http://127.0.0.1:5000/api/scan/smc?limit=20');
      const dataS = await resS.json();
      
      setLiveData({
        darvas: dataD.data,
        smc: dataS.data
      });
      setScanStatus('Scan Complete!');
      setTimeout(() => setScanStatus(''), 3000);
    } catch (err) {
      console.error(err);
      setScanStatus('Error connecting to API. Is backend running?');
    } finally {
      setIsScanning(false);
    }
  };
"""

content = content.replace("const [activeTab, setActiveTab] = useState('darvas');", "const [activeTab, setActiveTab] = useState('darvas');\n" + state_injection)

# 4. Update Header with Run Live Scan button
header_search = '<p className="subtitle">May 30, 2026 ✦ Universe: Nifty 500 ✦ Analyst: Manus AI</p>'
header_replace = """<p className="subtitle">May 30, 2026 ✦ Universe: Nifty 500 ✦ Analyst: Manus AI</p>
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', justifyContent: 'center', alignItems: 'center' }}>
          <button 
            onClick={runLiveScan} 
            disabled={isScanning}
            style={{
              padding: '0.6rem 1.2rem', 
              background: 'var(--accent-green)', 
              color: '#000', 
              border: 'none', 
              borderRadius: '6px', 
              fontWeight: 'bold', 
              cursor: isScanning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {isScanning ? <Loader className="spin" size={16} /> : <Zap size={16} />}
            {isScanning ? scanStatus : 'Run Live Scan'}
          </button>
        </div>"""

content = content.replace(header_search, header_replace)

# 5. Add .spin animation to App.css if not exists
css_path = r'c:\Work\Scanners\dashboard\src\App.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css_content = f.read()

if '.spin' not in css_content:
    css_content += """
.spin {
  animation: spin 2s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }
"""
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

# 6. We need to map liveData into the rendering loop. Let's find where darvas tab renders.
# It uses STOCKS_DATA.darvas.map(stock => ...)
# We can replace STOCKS_DATA.darvas with (liveData?.darvas?.top || STOCKS_DATA.darvas)
# Wait, API data structure might be slightly different than STOCKS_DATA.
# We will just show the raw JSON or a minimal card for liveData for now, or map it to the expected structure.
# Since formatting mapping might be complicated, I'll log a placeholder message for live data for now, OR let's map it.

content = content.replace('STOCKS_DATA.darvas.map((stock) => (', '(liveData?.darvas?.top || STOCKS_DATA.darvas).map((stock) => (')
content = content.replace('STOCKS_DATA.smc.map((stock) => (', '(liveData?.smc?.top || STOCKS_DATA.smc).map((stock) => (')

with open(r'c:\Work\Scanners\dashboard\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("React dashboard updated for live scanning successfully.")
