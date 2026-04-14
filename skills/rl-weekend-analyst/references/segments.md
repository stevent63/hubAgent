# Segment Definitions Reference

This file contains the precise filter criteria for every analytical segment across the 5 visualizations. When running the pipeline, apply these filters to the parsed data exactly as specified.

---

## Visualization 1: Core Universe Dashboard

### Segment 1.1: Regime Census
- **Filter**: None (full universe)
- **Group by**: mode_daily (DG, LG, DR, LR, B2B)
- **Output**: Count and percentage per bucket
- **Compare**: Prior week counts — compute delta and direction
- **Interpretation**: Rising DG% + falling DR% = market breadth improving. Opposite = deteriorating. LR rising = more reversal attempts in progress.

### Segment 1.2: Regime Flips
- **Filter**: Names where mode_daily ≠ prior_week_mode_daily
- **Group by**: Flip type (source_mode → target_mode)
- **Priority flip types** (in order of importance):
  1. DR → LR: Bear trend, momentum turning positive (early reversal attempt)
  2. LR → DG: Momentum confirmed, crossed RevL (bullish confirmation)
  3. LR → B2B: Weekly bear to bull transition beginning
  4. DG → LG: Momentum fading in uptrend (watch for top)
  5. LG → DR: Lost RevL support AND momentum declining (breakdown)
  6. Any → DR: New breakdowns
- **Output**: Top 20 flips sorted by R, grouped by flip type

### Segment 1.3: RevL Proximity
- **Filter**: |close - revl| / revl < 0.03 (within 3% of RevL)
- **Split by**: mode_daily
- **Priority names**:
  - LR mode + within 3% of RevL = "reclaim candidates" (about to cross bullish)
  - LG mode + within 3% of RevL = "don't lose it" (about to lose support)
  - DR mode + within 3% of RevL = "rejected at RevL" (bearish continuation)
- **Output**: Lists per category, sorted by R descending

### Segment 1.4: Extended Winners
- **Filter**: mode_daily == DG AND days_in_trend > 20 AND pl > 25
- **Sort by**: pl descending
- **Flag**: Any with MoM declining vs prior week (momentum exhaustion signal)
- **Output**: Top 15, with MoM direction annotation

### Segment 1.5: Capitulation Zone
- **Filter**: mode_daily == DR AND days_in_trend > 30 AND pl < -15
- **Sort by**: pl ascending (worst first)
- **Flag**: Any with MoM inflecting positive (potential reversal)
- **Output**: Full list with MoM direction annotation

---

## Visualization 2: Switch Universe

**Pre-filter**: mode_daily == DG AND mode_weekly == LR

### Segment 2.1: Fresh Tension
- **Filter**: weeks_in_trend < 10 AND mom > 3
- **Sort by**: mom descending
- **Why this matters**: Weekly bear is young, daily is already ripping. Shortest path to double green. Highest conviction Switch setups.
- **Output**: Full list with R, MoM, weeks, P/L

### Segment 2.2: Proving Ground (Value)
- **Filter**: weeks_in_trend BETWEEN 10 AND 20 AND pl < 20
- **Sort by**: r descending
- **Why this matters**: Enough duration to be meaningful, not yet rewarded. Best risk/reward entry window.
- **Output**: Full list with R, MoM, weeks, P/L

### Segment 2.3: Proving Ground (Extended)
- **Filter**: weeks_in_trend BETWEEN 10 AND 20 AND pl >= 20
- **Sort by**: pl descending
- **Why this matters**: Same setup as 2.2 but already ran. Entry risk is higher. Position sizing should be smaller.
- **Output**: Full list with R, MoM, weeks, P/L

### Segment 2.4: Late Recovery
- **Filter**: weeks_in_trend > 20 AND mom > 2
- **Sort by**: mom descending
- **Why this matters**: Long-duration bears showing signs of life. Higher risk — need fundamental catalyst to justify. But if they turn, the multi-year reversal is enormous.
- **Output**: Full list, flagged with sector clusters

### Segment 2.5: Ultra-Long Group Strength
- **Filter**: weeks_in_trend > 40
- **Group by**: Clusters of 3+ names within ±5 weeks of each other
- **Why this matters**: Sector-level bottoming, not random. Much higher conviction than isolated names.
- **Output**: Cluster groups with shared theme annotation

### Segment 2.6: Positive R Overlay
- **Filter**: r > 0 (applied across ALL Switch names)
- **Cross-reference**: Which names from segments 2.1-2.5 have positive R?
- **Why this matters**: Positive R = outperforming peers despite being in weekly bear. This is the quality filter. A Switch candidate with positive R is significantly higher quality than one with negative R.
- **Output**: R-positive subset with segment membership flags

---

## Visualization 3: Top Momentum (MoM 7-10)

**Pre-filter**: mom >= 7

### Segment 3.1: Fresh Leaders
- **Filter**: mom > 8 AND pl < 15
- **Sort by**: mom descending
- **MUST split by daily mode before interpreting P/L:**
  - **DG/LG mode + MoM >8 + P/L <15%**: Genuine fresh leaders. Bullish mode, strong momentum, haven't run yet. P/L = actual gains, and low P/L = early. Best new entry zone.
  - **DR/LR mode + MoM >8 + P/L <15%**: NOT fresh leaders despite high MoM. The name is in a bearish regime. P/L <15% means it hasn't fallen far yet (shallow decline). The high MoM may be a bear-market bounce or a momentum oscillator divergence. Treat these as speculative bounce candidates, not momentum leaders.
- **Signal context**: If signal is spBuy/dBuy, the name is flagged as weak regardless of MoM. High MoM + spBuy = the system sees strong short-term momentum in a fundamentally weak name. These are the most dangerous false positives — they look like leaders but are countertrend bounces.

### Segment 3.2: Sweet Spot
- **Filter**: mom BETWEEN 8.5 AND 9.5 AND pl BETWEEN 15 AND 35 AND mode_daily IN (DG, LG)
- **Sort by**: r descending
- **Why this matters**: Proven momentum AND proven P/L delivery in bullish mode. Not yet extended. This is the optimal entry zone for momentum-following positions. Names in DR/LR mode are EXCLUDED — their P/L represents decline depth, not reward.

### Segment 3.3: Extended Leaders
- **Filter**: mom > 9 AND pl > 40 AND mode_daily IN (DG, LG)
- **Sort by**: pl descending
- **Why this matters**: Trailing stop territory only. Don't initiate. Watch for MoM deceleration week-over-week as the first exit warning. Names in DR/LR mode are EXCLUDED — 40%+ P/L in bear mode = deeply crashed names with countertrend momentum, which is a completely different (and much riskier) setup.

### Segment 3.4: Fading Momentum
- **Filter**: mom BETWEEN 7 AND 8
- **Split by**: mode_daily first, then by pl
- **In bullish modes (DG/LG)**: High P/L + fading MoM = potential distribution top. Low P/L + fading MoM = weak trend likely to drop off list.
- **In bearish modes (DR/LR)**: These are countertrend bounces losing steam. High P/L = deep decline that bounced but is now fading. Treat as exit/avoid, not as a "fading leader."

### Segment 3.5: Sector Heatmap
- **Filter**: All MoM 7-10 names
- **Group by**: sector/theme
- **Count**: Names per sector, average MoM per sector, average P/L per sector
- **Compare**: Prior week sector counts (which sectors gained/lost representation)
- **Output**: Sector table sorted by name count, with WoW change annotation

---

## Visualization 4: Daily Buy Mode

**Pre-filter**: Names currently in daily buy mode (signal contains Buy/spBuy/dBuy/wBuy)

**CRITICAL**: This universe contains TWO fundamentally different populations mixed together:
1. **Trend-following buys** (Buy, wBuy) — names already in bullish modes (DG, LG, B2B). P/L = gains since bullish flip. Positive P/L = strength.
2. **Mean reversion buys** (spBuy, spBuy+, spBuy++, dBuy) — names in bearish modes (DR, LR). P/L = depth of decline since bearish flip. Positive P/L = how far the name has FALLEN. High P/L = deeper weakness, NOT better delivery.

Every segment below MUST split analysis by signal type and interpret P/L accordingly. Never combine spBuy and Buy names into a single "strongest performers" ranking.

### Segment 4.1: Fresh Flips (Day 1-3)
- **Filter**: days_in_trend <= 3
- **Split by**: Signal type — trend-following (Buy, wBuy, pP) vs mean reversion (spBuy variants, dBuy)
- **For trend-following**: Group by mode — DG/LG/B2B. Positive P/L = actual gains. These are confirmations.
- **For mean reversion**: Group by mode — DR/LR. P/L measures depth of decline. spBuy++ in DR = most deeply oversold. These are speculative bounce candidates, NOT confirmations of strength.
- **Why this matters**: The MIX of signal types tells you about market character. Heavy mean reversion concentration = the market is generating lots of oversold signals = broad weakness producing bounce candidates. Heavy trend-following concentration = the market is confirming existing uptrends = healthier breadth.

### Segment 4.2: Proving Phase (Day 4-10)
- **Filter**: days_in_trend BETWEEN 4 AND 10
- **Split by**: Signal type, then by MoM direction
- **For trend-following buys**: Rising MoM = confirming. Flat/declining MoM = trend losing steam.
- **For mean reversion buys**: The question is different — has the bounce materialized? Check if mode has changed (DR→LR or LR→DG = bounce working). If still in DR/LR after 4-10 days with the same or worse MoM, the mean reversion signal is failing. High P/L here means the stock has continued falling DESPITE the buy signal = signal failure, not strong delivery.

### Segment 4.3: Established (Day 10-20)
- **Filter**: days_in_trend BETWEEN 10 AND 20
- **For trend-following buys**: Use P/L pace (pl / days_in_trend) as a quality metric. Low pace = anemic trend.
- **For mean reversion buys**: P/L pace is INVERTED — high pace means the stock is falling faster, which is BAD. Instead, check: has the name's mode improved since signal fired? DR→LR→DG progression = mean reversion working. Still in DR at day 10+ = the bounce thesis has failed. These should be flagged as signal failures, not held as established buys.

### Segment 4.4: Extended (Day 20+)
- **Filter**: days_in_trend > 20
- **Sort by**: days_in_trend descending
- **For trend-following buys**: Hold and trail territory. Monitor for exhaustion. NOT new entry candidates.
- **For mean reversion buys at day 20+**: If still in DR/LR mode, this is a failed signal with extreme duration. The name has been declining for 20+ days since the system flagged it as a bounce candidate. These are NOT "extended buys" — they are zombie signals in broken names. Flag them explicitly as failures.

### Segment 4.5: Signal Type Distribution
- **Filter**: All daily buy mode names
- **Count**: By signal type, split into trend-following vs mean reversion
- **Key ratios**:
  - Mean reversion signals / total buy signals (high = broad weakness generating oversold bounces)
  - Trend-following signals / total buy signals (high = healthy breadth confirming uptrends)
  - Mean reversion signals where mode has improved since signal fired / total mean reversion signals (= bounce success rate)
- **Compare**: Prior week ratios
- **Interpretation**: Rising mean reversion ratio = market getting weaker, more names falling into oversold. Rising trend-following ratio = market getting healthier. High bounce success rate = the mean reversion signals are working. Low bounce success rate = the selling pressure is overwhelming the bounce attempts.

---

## Visualization 5: Trend Length vs Momentum (R Color)

### Segment 5.1: Triple Crown
- **Filter**: r > 0 AND mom > 7 AND days_in_trend < 15
- **Sort by**: r descending
- **Why this matters**: The best names in the entire universe. Strong relative strength, strong momentum, early in trend. These should be in every idea generation pass.

### Segment 5.2: High R, Fading Momentum
- **Filter**: r > 0 AND mom < 5 AND prior_week_mom > mom (MoM declining)
- **Sort by**: r descending
- **Why this matters**: Still outperforming peers but momentum is fading. Watch for MoM re-acceleration (buy) or continued decline (exit/reduce).

### Segment 5.3: Negative R, Rising Momentum
- **Filter**: r < 0 AND mom > 5
- **Sort by**: mom descending
- **Why this matters**: Underperforming peers historically but momentum is turning. Potential rotation candidates. Need to see R cross positive to confirm.

### Segment 5.4: R Inflection Points
- **Filter**: r > 0 AND prior_week_r <= 0 (crossed from negative to positive this week)
- **Sort by**: mom descending
- **Why this matters**: Relative strength regime change. These names just started outperforming. If accompanied by buy signal, very high conviction.

### Segment 5.5: R Deterioration
- **Filter**: r < 0 AND prior_week_r >= 0 (crossed from positive to negative this week)
- **Sort by**: r ascending
- **Why this matters**: Losing relative strength leadership. If currently in portfolio, evaluate whether to reduce. If on watchlist, move to WATCH or remove.

### Segment 5.6: Pullback-in-Strength (Buyable Dips in Quality Names)

This segment captures names with proven relative strength leadership that are experiencing a *daily-timeframe* pullback while their *weekly* trend remains intact. These are NOT breakdowns — they are reloads in strong names.

- **Filter**: r > 0.5 AND mode_daily IN (DR, LR) AND mode_weekly IN (LG, DG) AND mom_daily < 0
- **Sort by**: r descending
- **Why this matters**: High R = the name has been a persistent outperformer. Daily DR/LR = it's pulling back. Weekly LG/DG = the intermediate trend hasn't broken. Negative daily MoM = the pullback is active, not yet resolved. This combination identifies quality names "on sale." The thesis is that the weekly trend reasserts and the daily flips back to bullish.

**Sub-segments** (analyze each separately):

#### 5.6a: Shallow Pullback (daily LR, weekly DG)
- **Filter**: mode_daily == LR AND mode_weekly == DG AND r > 0.5
- **Sort by**: r descending, then by daily MoM ascending (least negative = closest to turning)
- **Read**: The mildest version — daily momentum is bearish but still LR (rising within bear). Weekly is full DG. These are the shallowest dips and often the first to resolve back to DG. Names with MoM approaching zero are about to flip.
- **Entry signal**: Daily MoM crosses positive (LR → DG flip) while weekly DG holds.

#### 5.6b: Deep Pullback (daily DR, weekly LG)
- **Filter**: mode_daily == DR AND mode_weekly == LG AND r > 0.5
- **Sort by**: r descending
- **Read**: Deeper pullback — daily momentum is falling within a bear mode, but weekly trend is still bullish (LG = bull, momentum fading). These need more time. Watch for daily MoM to inflect positive (DR → LR flip) as the first recovery signal.
- **Entry signal**: Daily mode flips from DR to LR (momentum inflection). NOT when it's still falling.

#### 5.6c: Deep Pullback in Strong Weekly (daily DR, weekly DG)
- **Filter**: mode_daily == DR AND mode_weekly == DG AND r > 0.5
- **Sort by**: r descending
- **Read**: The most dislocated version — daily is in full bear mode but weekly is full bullish. Maximum tension. These either snap back hard or the weekly trend is about to break. Check if the name has a buy signal (spBuy = countertrend bounce attempt in progress). Higher risk but highest reward if the weekly DG holds.
- **Entry signal**: spBuy or better signal + MoM inflection. Size smaller than 5.6a setups.

**Sector grouping is critical for this segment.** When 3+ names from the same sector appear in 5.6b/5.6c simultaneously, it's a *sector-level pullback* — much higher conviction than isolated names. The March 14, 2026 report showed precious metals miners (AG, HL, TGB, PAAS) all clustering in 5.6b — a textbook sector dip-buy setup.

**Convergence bonus**: Pullback-in-strength names that ALSO carry an active spBuy signal get +2 convergence points. They have both the structural quality (high R, weekly trend intact) and the signal confirmation (system recognizes the bounce).

**Kill condition for the segment**: Weekly mode flips from DG/LG to LR or DR. Once the weekly breaks, the pullback thesis is dead — it's a breakdown, not a dip.

**Output format**:
```
## Pullback-in-Strength — [date]

### Sector Clusters (3+ names from same sector)
[Group name] — [names] — avg R, avg MoM, weekly mode
  → Sector dip-buy? Y/N based on weekly holding + catalyst intact

### 5.6a Shallow Pullbacks (LR daily / DG weekly) — [count]
[table sorted by R, annotated with distance to MoM=0]

### 5.6b Deep Pullbacks (DR daily / LG weekly) — [count]
[table sorted by R, flagged if spBuy signal present]

### 5.6c Maximum Dislocation (DR daily / DG weekly) — [count]
[table sorted by R, flagged if spBuy signal present]
```
