# Scoring & Calibration Reference

This file defines how ideas are scored against outcomes and how the system calibrates over time.

---

## Scoring an Idea

Ideas are scored when ONE of the following occurs:
1. **TARGET HIT**: Price reaches target price within timeframe
2. **STOPPED OUT**: Price hits stop level
3. **KILL CONDITION MET**: A specified kill condition fires (even if stop isn't hit)
4. **EXPIRED**: Timeframe elapsed without target or stop being hit
5. **STILL OPEN**: Idea is within timeframe and neither target nor stop has been reached

### Scoring Fields

```json
{
  "id": "2026-03-14-DKNG-L",
  "outcome": "TARGET_HIT | STOPPED_OUT | KILL_CONDITION | EXPIRED | STILL_OPEN",
  "date_scored": "2026-03-28",
  "days_held": 14,
  "actual_pnl_pct": 18.5,
  "actual_pnl_r": 2.3,
  "probability_estimate": 0.65,
  "was_correct": true,
  "peak_favorable": 22.1,
  "peak_adverse": -4.2,
  "kill_condition_fired": null,
  "notes": "Hit target in 8 trading days. Momentum accelerated post Investor Day."
}
```

### Binary Outcome for Calibration

For calibration purposes, an idea is "correct" if:
- LONG: Price reached target OR P/L was positive at expiry
- SHORT: Price reached target OR P/L was positive at expiry

An idea is "incorrect" if:
- STOPPED OUT
- KILL CONDITION MET (resulting in loss)
- EXPIRED with negative P/L

---

## Calibration Metrics

### 1. Hit Rate
Simple percentage of ideas that were "correct."

```
hit_rate = correct_ideas / total_scored_ideas
```

**Target**: 55-65% for HIGH tier, 45-55% for MEDIUM tier.

### 2. Brier Score
Measures calibration of probability estimates. Lower is better.

```
brier_score = (1/N) * Σ(probability_estimate - actual_outcome)²
```

Where actual_outcome is 1 (correct) or 0 (incorrect).

**Target**: < 0.25 (well-calibrated), < 0.20 (excellent)

**Interpretation**:
- If Brier score is high and hit rate is low → probability estimates are too optimistic
- If Brier score is high and hit rate is high → probability estimates are too conservative
- If Brier score is low → probability estimates are well-calibrated regardless of hit rate

### 3. Average EV Realized

```
avg_ev_realized = mean(actual_pnl_r) across all scored ideas
```

**Target**: > 0.5R (the system is generating positive expected value)

### 4. Calibration by Tier

Track metrics separately for HIGH, MEDIUM, and WATCH tiers.

```json
{
  "HIGH": { "count": 12, "hit_rate": 0.67, "avg_pnl_r": 1.2, "brier": 0.18 },
  "MEDIUM": { "count": 18, "hit_rate": 0.50, "avg_pnl_r": 0.4, "brier": 0.22 },
  "WATCH": { "count": 8, "hit_rate": 0.38, "avg_pnl_r": -0.3, "brier": 0.28 }
}
```

This validates whether the tiering system is working. HIGH should outperform MEDIUM, which should outperform WATCH.

### 5. Segment Effectiveness

Track which segments are most predictive of positive outcomes.

```json
{
  "switch_fresh_tension": { "appearances": 15, "win_rate": 0.67 },
  "triple_crown": { "appearances": 8, "win_rate": 0.75 },
  "mom_sweet_spot": { "appearances": 22, "win_rate": 0.55 },
  "r_inflection_positive": { "appearances": 11, "win_rate": 0.64 }
}
```

Over time, this tells us which segments to weight more heavily in convergence scoring.

### 6. Theme Effectiveness

Track which themes produce the best ideas.

```json
{
  "software_saas": { "ideas": 8, "hit_rate": 0.63, "avg_pnl_r": 0.9 },
  "defense_space": { "ideas": 5, "hit_rate": 0.80, "avg_pnl_r": 1.5 },
  "gold_miners": { "ideas": 6, "hit_rate": 0.50, "avg_pnl_r": 0.3 }
}
```

---

## Calibration Adjustments

After accumulating ≥ 20 scored ideas, begin adjusting the probability estimation framework:

### Step 1: Check Overall Calibration
- If average probability estimate > hit rate by >10%: reduce all base rates by 5%
- If average probability estimate < hit rate by >10%: increase all base rates by 5%

### Step 2: Check Segment Weights
- If a segment's win rate > 65%: increase its convergence weight from +1 to +1.5
- If a segment's win rate < 40%: decrease its convergence weight from +1 to +0.5
- If a segment's win rate < 30% after 10+ appearances: consider removing it as a convergence signal

### Step 3: Check Theme Bias
- If a theme consistently underperforms: apply a -5% probability adjustment for ideas in that theme
- If a theme consistently outperforms: apply a +5% probability adjustment

### Step 4: Check Risk/Reward Execution
- Track how often targets vs stops are hit
- If stops are hit more than expected: targets may be too aggressive or stops too tight
- Adjust the R/R framework accordingly

---

## Minimum Sample Sizes

- **Start reporting calibration**: After 10 scored ideas
- **Start adjusting base rates**: After 20 scored ideas
- **Start adjusting segment weights**: After 30 scored ideas (need per-segment sample)
- **Start adjusting theme weights**: After 40 scored ideas

Until these thresholds are met, use the default probability framework from the SKILL.md.

---

## Weekly Calibration Report Format

Include this at the bottom of every pipeline report once ≥ 10 ideas have been scored:

```
## Calibration Dashboard

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Scored | 24 | — | — |
| Overall Hit Rate | 58% | 55-65% | ON TARGET |
| Brier Score | 0.21 | <0.25 | GOOD |
| Avg EV Realized | 0.7R | >0.5R | ON TARGET |
| HIGH Tier Hit Rate | 67% | >60% | ON TARGET |
| MEDIUM Tier Hit Rate | 50% | >45% | ON TARGET |

### Top Performing Segments
1. triple_crown: 75% win rate (8 appearances)
2. switch_fresh_tension: 67% win rate (15 appearances)
3. r_inflection_positive: 64% win rate (11 appearances)

### Underperforming Segments
1. mom_fading: 33% win rate (6 appearances) ← consider de-weighting
2. switch_late_recovery: 40% win rate (10 appearances) ← needs fundamental filter

### Recommended Adjustments
- Increase convergence weight for triple_crown from 1.0 to 1.5
- Add mandatory fundamental alignment requirement for switch_late_recovery ideas
```
