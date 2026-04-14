---
name: rl-buy-signals-viz
description: Generate an interactive HTML dashboard visualizing buy signals from RL (RevL) trading dashboard HTML files. Trigger when the user uploads an RL HTML file and asks to visualize, chart, or dashboard buy signals from the Action column. Handles signal types spBuy++, spBuy+, spBuy, dBuy, Buy, wBuy. Produces scatter plots, bar charts, mode distribution, and a sortable ticker table. Also trigger when user says "buy signals dashboard", "buy signals viz", or references this saved format.
---

# RL Buy Signals Visualization

Generate an interactive dark-themed HTML dashboard from uploaded RL daily HTML files.

## Workflow

1. **Extract** buy signals using `scripts/extract_buy_signals.py`:
   ```bash
   python3 /path/to/scripts/extract_buy_signals.py <uploaded_rl_file.html> /home/claude/buy_signals.json
   ```

2. **Build the dashboard** by embedding extracted JSON into the HTML template:
   ```python
   import json
   with open('/home/claude/buy_signals.json') as f:
       data = json.load(f)
   json_str = json.dumps(data, separators=(',', ':'))

   with open('/path/to/assets/template.html') as f:
       html = f.read()

   html = html.replace('%%DATA_PLACEHOLDER%%', json_str)

   with open('/mnt/user-data/outputs/RL_Buy_Signals_YYYYMMDD.html', 'w') as f:
       f.write(html)
   ```

3. **Present** the output file and provide a brief analysis summary.

## Analysis Summary Guidelines

After generating the dashboard, provide a concise summary covering:

- **Signal counts** by type (spBuy++ through wBuy)
- **Top spBuy++/spBuy+ names** — highlight strongest reversal candidates
- **Mode bucket distribution** — how many Bear→Bull Flips vs Light Red vs Dark Red
- **Switch candidates** — names with positive R in weekly bear trends (key for the Switch Strategy)
- **Thematic clusters** — sectors/themes with concentrated buy signals (housing, REITs, tech, financials, etc.)

## Signal Hierarchy (strongest → weakest)

spBuy++ > spBuy+ > spBuy > dBuy > Buy > wBuy

## Mode Bucket Mapping (from HTML cell CSS classes)

- c4 = Dark Green (bull + rising MoM)
- c5 = Light Green (bull + fading MoM)
- c6 = Dark Red (bear + falling MoM)
- c7 = Light Red (bear + rising MoM)
- c20 = Bear→Bull Flip
- c21 = Bear→Bull (LR→LG)

## Dashboard Components

1. **Stats row** — count per signal type with color coding
2. **P/L vs Days scatter** — signal-colored dots, labels on spBuy+ and above
3. **Signal × Mode distribution** — stacked bar showing signal mix within each mode bucket
4. **Tr vs P/L scatter** — weekly bear duration vs P/L for switch candidate scanning
5. **Signal strength bars** — horizontal bars + asset class breakdown
6. **Sortable ticker table** — all signals with filtering by asset class, signal type, and search

## Output Naming

`RL_Buy_Signals_YYYYMMDD.html` — extract the date from the uploaded filename when possible.
