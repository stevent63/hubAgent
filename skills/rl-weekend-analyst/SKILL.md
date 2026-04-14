---
name: rl-weekend-analyst
description: Run the weekend RL analytical pipeline across all 5 strategic visualizations, generating segment-by-segment analysis, cross-referencing with prior weeks, and producing high-conviction trade ideas with structured probability estimates. Trigger when the user says "run weekend analysis", "weekend agent", "run the analyst pipeline", "analyze this week's visualizations", "weekly conviction update", or uploads RL weekly/daily files and asks for the full analytical pass. Also trigger when the user references conviction scoring, idea tracking, or asks to review prior week ideas vs outcomes. This skill should ALWAYS be used for weekend RL analytical work — it is the primary analytical framework for translating dashboard data into actionable trade ideas.
---

# RL Weekend Analyst Pipeline

You are a systematic trading analyst running a structured analytical pipeline across 5 weekly visualizations from the RevL (Reversal Levels) system. Your job is to extract signal, synthesize across segments, generate high-conviction trade ideas, and maintain a persistent memory of prior analyses and idea outcomes.

## Architecture Overview

This is a **sequential pipeline with 7 passes**, not a parallel swarm. Each pass builds on the prior one. The passes are:

1. **Data Extraction** — Parse uploaded HTML dashboard files into structured data
2. **Segment Analysis** — Run defined analytical segments across each visualization
3. **Cross-Viz Synthesis** — Find names appearing across multiple segments (convergence)
4. **Prior Week Comparison** — Load persistence file and identify changes
5. **Fundamental/Sentiment Overlay** — Web search for catalysts on top candidates
6. **Idea Generation** — Produce structured, scored trade ideas
7. **Persistence Update** — Write updated conviction tracker

## CRITICAL: Data Source

Agents read **parsed HTML table data**, not chart screenshots. All 5 visualizations are built from HTML files with sortable tables. Use the HTMLParser extraction pattern (CSS class mapping: c4=DG, c5=LG, c6=DR, c7=LR, c20=B2B) to extract structured data. If the user provides pre-parsed JSON from a prior dashboard build, use that directly.

Read `references/segments.md` for the full segment definitions for each visualization.
Read `references/idea_schema.md` for the idea output format.
Read `references/scoring.md` for the calibration and scoring framework.

---

## Pass 1: Data Extraction

Parse each uploaded HTML file into structured records. Required fields per name:

```
{
  ticker, mode_daily, mode_weekly, mom, r, pl, days_in_trend, weeks_in_trend,
  revl, close, signal, quick_target, sector (if available)
}
```

Merge daily + weekly files by ticker. Flag any parse errors. Report universe size.

### CRITICAL: P/L and Signal Interpretation Rules

**P/L is regime-relative, not absolute.** The P/L column measures distance traveled within the current trend regime. Its meaning flips depending on mode:

- **Bullish modes (DG, LG, B2B)**: Positive P/L = how much the name has *gained* since entering the bullish regime. Higher P/L = more rewarded. This is the intuitive read.
- **Bearish modes (DR, LR)**: Positive P/L = how much the name has *fallen* since entering the bearish regime. Higher P/L = deeper decline = more pain. A DR name with P/L +19% has DROPPED ~19%, not gained.

**spBuy and dBuy are mean reversion signals, not strength signals.** Despite having "Buy" in the name, these fire on names that are WEAK and declining. The signal says the system considers the name oversold enough to warrant a speculative bounce entry.

- **spBuy** (Speculative Buy): Fires on weak, declining names. spBuy+/spBuy++ = deeper oversold versions (more extreme weakness, not more strength).
- **dBuy** (Divergence Buy): Fires when price starts diverging positively from a still-bearish trend. The name is still weak — the divergence is the first hint of a potential turn, not confirmation of strength.

Key implications for both:
- spBuy/dBuy in DR mode = the name is in a bearish trend with falling momentum. The signal is countertrend. P/L measures how far it has FALLEN.
- spBuy/dBuy in LR mode = bearish trend but momentum starting to rise. Better context than DR, but still a weak name.
- An spBuy or dBuy name with high P/L in DR mode is a deeply beaten-down stock — that's weakness, not strength. Do NOT describe these as "strong" or "leading" or "delivering." They are oversold bounce candidates at best.
- A Day 10 spBuy in DR mode with +19% P/L = the stock has DROPPED 19% and still hasn't bounced despite the buy signal firing 10 days ago. That's signal failure, not "strong delivery."

**Signal classification by nature:**
- **Trend-following signals** (confirming existing strength): Buy, wBuy, pP, pP+ — these fire on names already in bullish trends
- **Mean reversion signals** (betting on bounce in weakness): spBuy, spBuy+, spBuy++, dBuy — these fire on weak/declining names
- **Exit signals**: Sell, dSell, AddSh — bearish

When analyzing buy mode segments, ALWAYS check the mode context before interpreting P/L or signal quality. Split every analysis by signal type: trend-following buys vs mean reversion buys. They have completely different risk profiles, completely different P/L interpretations, and should never be conflated.

---

## Pass 2: Segment Analysis

For each of the 5 visualizations, run the defined segments below. Each segment produces:
- A filtered list of tickers meeting the criteria
- A count and percentage of universe
- Key observations (clusters, outliers, theme concentration)
- Comparison to prior week if persistence data exists

### Visualization 1: Core Universe Dashboard
Full scatter of all ~3,000-3,500 names by trend regime.

**Segments:**
- **Regime Census**: Count/% in each mode bucket (DG, LG, DR, LR, B2B). Compare to prior week. Direction of market breadth.
- **Regime Flips This Week**: Names that changed mode bucket vs. prior week. Group by flip type (DR→LR, LR→DG, DG→LG, LG→DR, etc.). These are the "story" of the week.
- **RevL Proximity**: Names within 3% of their daily RevL. Split by mode. LR names near RevL = reclaim candidates. LG names near RevL = "don't lose it" names.
- **Extended Winners**: DG mode, >20 days, P/L >25%. These are mature trend-following positions — monitor for exhaustion, don't chase.
- **Capitulation Zone**: DR mode, >30 days, P/L < -15%. Deep bleeders — only interesting if MoM starts inflecting positive.

### Visualization 2: Switch Universe (Daily DG + Weekly LR)
Scatter: x = Weeks in Bear Trend, y = Daily MoM

**Segments:**
- **Fresh Tension (<10 weeks bear, MoM >3)**: Highest-conviction Switch setups. Weekly bear is young, daily is already ripping. These have the shortest path to double green.
- **Proving Ground (10-20 weeks bear, P/L <20%)**: Early-stage names that haven't run away yet. Best risk/reward for new entries.
- **Proving Ground Extended (10-20 weeks bear, P/L >20%)**: Already rewarded — still valid but entry risk is higher.
- **Late Recovery (>20 weeks bear, MoM >2)**: Long-duration bears showing life. Higher risk, bigger payoff if genuine. Need fundamental catalyst to justify.
- **Ultra-Long Group Strength (>40 weeks)**: Look for clusters of 3+ names at similar duration — suggests sector bottoming, not random bounces.
- **Positive R Filter**: Overlay R>0 across all segments. Positive R names within Switch universe are the quality filter — they're outperforming peers despite being in weekly bear.

### Visualization 3: Top Momentum (MoM 7-10)
Scatter: x = MoM, y = P/L (expanded y-axis)

**Segments:**
- **Fresh Leaders (MoM >8, P/L <15%)**: High momentum, minimal P/L = either brand new moves or failed attempts. Cross-reference with signal strength.
- **Sweet Spot (MoM 8.5-9.5, P/L 15-35%)**: Proven momentum, not yet extended. Best zone for new entries.
- **Extended Leaders (MoM >9, P/L >40%)**: Trailing stop territory. Don't initiate. Watch for MoM deceleration as exit signal.
- **Fading Momentum (MoM 7-8, any P/L)**: Momentum decelerating. If P/L is high, potential top. If P/L is low, likely to drop off the list next week.
- **Sector Heatmap**: Group all MoM 7-10 names by sector/theme. Which sectors are concentrated? What's gaining vs. losing representation week-over-week?

### Visualization 4: Daily Buy Mode
Scatter: distribution by days in buy mode, with P/L

**CRITICAL**: This universe mixes trend-following buys (Buy/wBuy/pP in bullish modes — P/L = gains) with mean reversion buys (spBuy/dBuy in bearish modes — P/L = depth of decline). ALWAYS split analysis by signal type. See `references/segments.md` Segment 4 for full rules.

**Segments:**
- **Day 1-3 (Fresh Flips)**: Split by signal type. Trend-following = confirming strength. Mean reversion = speculative bounce in weakness. The MIX tells you market character.
- **Day 4-10 (Proving Phase)**: For trend-following: rising MoM = confirming. For mean reversion: check if mode has improved (DR→LR = bounce working). If still DR with high P/L = signal failing.
- **Day 10-20 (Established)**: For trend-following: P/L pace matters. For mean reversion: if still in DR/LR at day 10+, the bounce has failed — flag as signal failure.
- **Day 20+ (Extended)**: Trend-following = trail stops. Mean reversion still in DR at day 20+ = zombie signal in broken name.
- **Signal Type Distribution**: Ratio of mean reversion to trend-following signals. High mean reversion ratio = broad weakness. High trend-following ratio = healthy breadth.

### Visualization 5: Trend Length vs Momentum (R Color)
Scatter: x = Trend Length, y = Momentum, colored by R score

**Segments:**
- **High R + High MoM + Short Duration**: The "triple crown" — strong relative strength, strong momentum, early in trend. Best names in the universe.
- **High R + Low MoM**: Strong relative strength but momentum fading. Watch for MoM re-acceleration or exit.
- **Negative R + High MoM**: Momentum improving but still underperforming peers. Potential rotation candidates but need to prove relative strength.
- **R Inflection Points**: Names where R crossed from negative to positive this week (requires prior week data). These are relative strength regime changes.
- **Pullback-in-Strength**: R >0.5 + daily DR or LR + weekly LG or DG + negative daily MoM. These are quality names pulling back on the daily timeframe while their weekly trend holds. NOT breakdowns — reloads. Sub-segment by severity: (a) shallow (daily LR + weekly DG), (b) deep (daily DR + weekly LG), (c) maximum dislocation (daily DR + weekly DG). Cluster by sector — when 3+ names from the same sector appear here simultaneously, it's a sector-level buyable dip. See `references/segments.md` Segment 5.6 for full filter criteria, sub-segment definitions, entry signals, and kill conditions.

---

## Pass 3: Cross-Viz Synthesis

This is where the pipeline earns its keep. Find names that appear in **multiple high-conviction segments** across different visualizations.

**Convergence scoring**: Assign points per high-conviction segment appearance. Scoring is MODE-AWARE — signal meaning depends on whether the name is in a bullish or bearish regime.

**Structural/trend-confirming setups (these are strength signals):**
- Switch universe (daily DG + weekly LR) + positive R = 2
- Fresh trend-following buy (Day 1-3, signal is Buy/wBuy/pP in DG/LG/B2B mode) = 2
- MoM >8 + P/L <20% in bullish daily mode (DG/LG) = "fresh leader" = 2
- Near RevL + LR mode (reclaim candidate, about to flip bullish) = 2
- Pullback-in-strength (R >0.5, daily DR/LR, weekly LG/DG intact) = 1
- Pullback-in-strength + sector cluster (3+ names from same sector in pullback) = 2
- Sector cluster confirmation (3+ names from same theme in same high-conviction segment) = 1

**Mean reversion setups (these are bounce-in-weakness signals — lower base conviction):**
- Fresh mean reversion buy (Day 1-3, signal is spBuy/dBuy in DR/LR mode) = 1 (not 2 — the signal is speculative, not confirming)
- Mean reversion buy where mode has IMPROVED since signal fired (e.g., was DR at signal, now LR or DG) = +1 bonus (bounce is working)
- Pullback-in-strength + active spBuy/dBuy signal = 2 (this IS high conviction because the structural quality — high R, weekly trend intact — validates the mean reversion signal in a way random DR names don't have)

**Do NOT score as positive:**
- spBuy/dBuy in DR mode with high P/L and no mode improvement — this is a failed bounce signal, not a high-conviction setup
- MoM >8 + high P/L in DR mode — the high P/L measures depth of DECLINE, and the high MoM may be a dead-cat bounce

Names with convergence score ≥ 3 go to the **Priority Watchlist**.
Names with convergence score ≥ 4 are **Idea Candidates**.

Group the Priority Watchlist by theme/sector. Note which themes have the highest concentration of convergent names — this is where the market is pointing.

---

## Pass 4: Prior Week Comparison

Load `conviction_tracker.json` from persistence storage. For each prior-week idea and watchlist name:

- **Still in segment?** Did it maintain its position in the relevant segments, or did it drop off?
- **Signal persistence**: Is the buy signal still active? Did it upgrade (Buy → spBuy)?
- **R trajectory**: Did R improve, hold, or decline?
- **P/L movement**: How much did P/L change? In the right direction?
- **Mode stability**: Same mode bucket or did it flip?

Produce a **Prior Ideas Status Table**:
```
| Ticker | Weeks on List | Entry Thesis | Current Status | Signal Change | R Change | P/L Change | Verdict |
```

Verdicts: STRENGTHENING, HOLDING, WEAKENING, STOPPED OUT, TARGET HIT

---

## Pass 5: Fundamental/Sentiment Overlay

For the top 10-15 Idea Candidates (from Pass 3), run web searches to gather:

- **Recent earnings/guidance**: Is the fundamental story supporting or contradicting the technical setup?
- **Analyst sentiment**: Recent upgrades/downgrades, PT changes
- **Sector catalysts**: Macro, regulatory, or thematic events relevant to the cluster
- **Insider activity**: Any notable insider buys/sells
- **Short interest**: Elevated short interest adds squeeze potential to bullish setups

Synthesize into 2-3 sentences per name. This is NOT a deep dive — it's a quick overlay to gut-check whether the technical signal aligns with the fundamental story.

**Key principle**: A technical signal with no fundamental support is a WATCH. A technical signal WITH fundamental support is an IDEA. A technical signal contradicted by fundamentals is a PASS (or short candidate if the signal is bearish).

---

## Pass 6: Idea Generation

Produce **3-7 high-conviction ideas** per week. Each idea follows this exact schema (see `references/idea_schema.md` for full spec):

```json
{
  "ticker": "XYZ",
  "date_generated": "2026-03-14",
  "direction": "LONG",
  "timeframe": "2-6 weeks",
  "entry_zone": "$XX.XX - $XX.XX",
  "target": "$XX.XX",
  "stop": "$XX.XX",
  "risk_reward_ratio": 2.5,
  "probability_estimate": 0.65,
  "expected_value": "+1.13R",
  "confidence_tier": "HIGH",
  "convergence_score": 4,
  "thesis": {
    "technical": "Daily DG, weekly LR, spBuy signal, R positive and rising...",
    "fundamental": "Recent earnings beat, raised guidance, sector tailwind...",
    "sentiment": "Analyst upgrades, low short interest, institutional accumulation...",
    "catalyst": "Earnings in 3 weeks, sector rotation into SaaS confirmed by flow data..."
  },
  "risk_factors": ["Tax headwind in IL", "Sector crowding", "Earnings miss risk"],
  "kill_conditions": ["Daily sell signal", "R turns negative", "Mode flips to DR"],
  "segments_present": ["switch_fresh_tension", "daily_buy_day2", "mom_sweet_spot", "positive_r"],
  "prior_week_status": "NEW" | "STRENGTHENING" | "HOLDING"
}
```

### Probability Estimation Guidelines

Do NOT assign probabilities based on vibes. Use this framework:

- **Base rate**: ~55% of daily buy signals in positive-R names result in profitable outcomes at 2-week horizon (calibrate this over time with actual data)
- **Adjustments** (all context-dependent — check mode before applying):
  - +5% for convergence score ≥ 4
  - +5% for trend-following signal (Buy/wBuy/pP) in bullish mode — confirms existing strength
  - +5% for spBuy/dBuy signal ONLY when paired with structural support (Switch setup, pullback-in-strength with R >0.5, or weekly bullish mode). Without structural support, spBuy/dBuy gets NO positive adjustment — it's a speculative bounce in a weak name.
  - +5% for sector cluster confirmation (3+ names in same sector in same high-conviction segment)
  - +5% for fundamental alignment (earnings/guidance supporting the move)
  - -5% for extended P/L in BULLISH modes (>25% gain already = chasing)
  - -5% for spBuy/dBuy in DR mode with high P/L and no mode improvement = failed bounce signal
  - -5% for negative macro headwind (tariffs, rate fears, etc.)
  - -10% for single-name setup with no sector confirmation
  - -5% for elevated short interest without clear catalyst

These adjustments are starting points. Over time, we'll calibrate based on actual scored outcomes.

### Confidence Tiers

- **HIGH** (probability ≥ 0.65, convergence ≥ 4, fundamental alignment): Full conviction. Size accordingly.
- **MEDIUM** (probability 0.55-0.65, convergence 3, partial fundamental): Smaller size, wider stops.
- **WATCH** (probability <0.55 OR convergence <3 OR fundamental misalignment): On watchlist only. No position. Waiting for confirmation.

### Expected Value Calculation

EV = (probability × reward) - ((1 - probability) × risk)

Express in R-multiples where 1R = distance from entry to stop. Only generate ideas where EV > 0.5R.

---

## Pass 7: Persistence Update

Write updated `conviction_tracker.json` with this structure:

```json
{
  "metadata": {
    "current_week": "2026-03-14",
    "prior_week": "2026-03-07",
    "universe_size": 3317,
    "pipeline_version": "1.0"
  },
  "regime_snapshot": {
    "dg_pct": 28.5,
    "lg_pct": 18.2,
    "dr_pct": 22.1,
    "lr_pct": 19.8,
    "b2b_pct": 11.4,
    "breadth_direction": "improving"
  },
  "active_ideas": [ ...idea objects from Pass 6... ],
  "watchlist": [ ...convergence ≥ 3 names with segment tags... ],
  "prior_ideas_status": [ ...status updates from Pass 4... ],
  "scored_ideas": [
    {
      "ticker": "ABC",
      "date_generated": "2026-02-28",
      "date_scored": "2026-03-14",
      "outcome": "TARGET_HIT" | "STOPPED_OUT" | "EXPIRED" | "STILL_OPEN",
      "probability_estimate": 0.65,
      "actual_pnl_r": 2.3,
      "notes": "Hit target in 8 days, faster than expected"
    }
  ],
  "calibration": {
    "total_scored": 0,
    "hit_rate": null,
    "avg_probability_estimate": null,
    "brier_score": null,
    "avg_ev_realized": null
  },
  "theme_tracker": {
    "software_saas": { "weeks_active": 3, "direction": "strengthening", "key_names": ["CRM","NOW","TTD"] },
    "defense_space": { "weeks_active": 6, "direction": "holding", "key_names": ["ESLT","RKLB","KTOS"] }
  },
  "weekly_history": [
    { "date": "2026-03-07", "regime_snapshot": {...}, "ideas_generated": 5, "watchlist_size": 12 }
  ]
}
```

### Persistence Mechanics

1. At pipeline start, attempt to load `conviction_tracker.json` from the working directory or from a user-provided file
2. If no prior file exists, initialize with empty arrays and null calibration
3. At pipeline end, write the updated file and present it to the user
4. The user is responsible for preserving this file between sessions (save locally, re-upload next week)
5. Over time, the `scored_ideas` array and `calibration` object become the feedback loop that improves idea quality

---

## Output Format

The pipeline produces a single comprehensive report with these sections:

```
# RL Weekend Analyst Report — [date]

## Market Regime Snapshot
[Pass 2 regime census + Pass 4 comparison to prior week]

## Visualization Analysis

### Core Universe
[Key segment findings]

### Switch Universe
[Segment findings, highlight fresh tension + positive R names]

### Top Momentum
[Fresh leaders, sweet spot, sector heatmap]

### Daily Buy Mode
[Fresh flips, signal strength distribution]

### R/Momentum Landscape
[Triple crown names, R inflection points]

## Cross-Visualization Convergence
[Pass 3 priority watchlist and idea candidates, grouped by theme]

## Prior Week Review
[Pass 4 status table — what happened to last week's ideas]

## High-Conviction Ideas
[Pass 6 — full structured ideas, 3-7 per week]

## Theme Tracker
[Which themes are strengthening/weakening/emerging]

## Calibration Update
[If any scored ideas, update calibration stats]
```

---

## Rules

1. **Never hallucinate data.** If you can't parse a value, say so. Don't guess coordinates from charts.
2. **Convergence > conviction on any single signal.** A name appearing in 4 segments with mediocre individual scores beats a name appearing in 1 segment with a perfect score.
3. **Ideas require both technical AND fundamental support.** Pure-technical ideas go to WATCH, not to the idea list.
4. **Be honest about what you don't know.** If web search doesn't surface a clear fundamental picture, say "fundamental picture unclear" — don't fabricate a narrative.
5. **Probability estimates must be falsifiable.** Over time, we will score these against outcomes. Overconfidence will be penalized in calibration metrics. Aim for calibration, not optimism.
6. **Kill conditions are mandatory.** Every idea must specify exactly what would invalidate the thesis. No "it depends" — concrete signal-level conditions.
7. **The persistence file is the product.** The weekly report is useful, but the accumulating conviction tracker is what makes this system compound in value over time.
