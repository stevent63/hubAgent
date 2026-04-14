#!/usr/bin/env python3
"""Extract buy signals from RL HTML dashboard files.

Usage: python3 extract_buy_signals.py <input.html> <output.json>
"""
import sys, json, re
from bs4 import BeautifulSoup

def extract(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    tables = soup.find_all('table')
    signals = []
    seen = set()

    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if 'Action' not in headers:
            continue
        ai = headers.index('Action')

        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) <= ai:
                continue
            action = cells[ai].get_text(strip=True)
            if not any(b in action for b in ['Buy', 'buy']):
                continue

            name = cells[0].get_text(strip=True)
            close = cells[2].get_text(strip=True) if len(cells) > 2 else ''
            tr = cells[3].get_text(strip=True) if len(cells) > 3 else '0'
            mc = cells[4].get('class', [''])[0] if len(cells) > 4 and cells[4].get('class') else ''
            mom_raw = cells[6].get_text(strip=True) if len(cells) > 6 else ''
            days = cells[7].get_text(strip=True) if len(cells) > 7 else '0'
            pl = cells[8].get_text(strip=True) if len(cells) > 8 else ''
            r_val = cells[10].get_text(strip=True) if len(cells) > 10 else ''

            r_m = re.search(r'(-?[\d.]+)', r_val)
            r_num = float(r_m.group(1)) if r_m else 0
            mom_m = re.search(r'(-?[\d.]+)', mom_raw)
            mom_num = float(mom_m.group(1)) if mom_m else 0
            pl_s = pl.replace('%','').replace('+','').strip()
            pl_num = float(pl_s) if pl_s.replace('-','').replace('.','').isdigit() else 0
            days_num = int(days) if days.isdigit() else 0
            tr_num = int(tr) if tr.isdigit() else 0
            sig = action.replace(' ','')

            mode_map = {'c4':'Dark Green','c5':'Light Green','c6':'Dark Red','c7':'Light Red',
                        'c20':'Bear-Bull Flip','c21':'Bear-Bull (LR-LG)'}
            mode = mode_map.get(mc, 'Unknown')

            # Asset class detection
            if any(x in name for x in ['ETF','ETN','ProShares','Direxion','iSh.','SPDR','iPath','Teucrium','Nuveen','Liberty All-Star']):
                ac = 'ETF'
            elif any(x in name for x in ['Bitcoin','Ethereum','Arweave','Helium','Render','THOR','Sandbox','Sui','Theta','Horizen','Decentraland','Internet Computer','Pi Network','Numeraire','Basic Attention','Berachain']):
                ac = 'Crypto'
            elif any(x in name for x in ['USDJPY','Chinese Yuan','Korean Won','Malaysian','EUR','GBP']):
                ac = 'FX'
            elif any(x in name for x in ['Australia','France','Soybean','Corn','Wheat','Gold','Silver','Crude','Natural Gas','Copper','Platinum']):
                ac = 'Macro'
            else:
                ac = 'Stock'

            key = f'{name}|{sig}|{pl}'
            if key not in seen:
                seen.add(key)
                signals.append({
                    'name': name, 'close': close, 'tr': tr_num,
                    'signal': sig, 'modeBucket': mode,
                    'mom': mom_num, 'days': days_num,
                    'pl': pl, 'plNum': pl_num,
                    'r': r_num, 'rRaw': r_val,
                    'assetClass': ac
                })
    return signals

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 extract_buy_signals.py <input.html> <output.json>")
        sys.exit(1)
    data = extract(sys.argv[1])
    with open(sys.argv[2], 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f"Extracted {len(data)} buy signals")
