# Signal Definitions

Complete specification for every RL signal type, including thresholds and action implications.

---

## Entry Signals

### Buy
- **Condition:** Price crossed RevL with confirming momentum
- **Mode typically:** Bear-Bull Flip or Dark Green
- **Action:** Enter at open or QT level
- **Hold until:** Sell, pP, or mode deterioration
- **Conviction:** High

### dBuy
- **Condition:** Developing Buy — earlier stage than full Buy
- **Mode typically:** Light Green, Bear-Bull (LR-LG)
- **Action:** Watch for upgrade to Buy; enter at reduced size or wait
- **Conviction:** Medium — lower than Buy

### spBuy / spBuy+ / spBuy++
- **Condition:** Bottom-fishing signal — price has capitulated in Dark Red
- **Mode:** Dark Red
- **Risk/reward:** High — these are counter-trend entries
- **Sizing:** 3–5% max per name
- **spBuy++** is the strongest bottom signal in the system
- **Universe signal:** spBuy count crossing 10% of total universe = capitulation threshold

### wBuy
- **Condition:** Weak Buy — marginal signal strength
- **Action:** Lowest entry conviction; consider only with strong theme/thesis support
- **Sizing:** Smaller than standard Buy position

---

## Exit Signals

### Sell
- **Condition:** Price broke below RevL
- **Action:** **HARD EXIT** — no hesitation, no averaging down, no "giving it one more day"
- **Execution:** Clean at open
- **Trust the system:** Sell = exit. Period.

### pP / pP+
- **Condition:** Extended momentum — profit-consideration signal
- **MoM context:** Typically fires when MoM is in +8 to +10 range, but NOT always at +10
- **Example:** ETR fired pP at MoM +8.89, not at +10
- **Action:** Take profits on winners
- **Nuance:** Not a hard exit — discretion allowed for tax/holding period considerations. But the system is saying "this winner is mature."
- **pP+** indicates higher urgency to take profits

### dSell
- **Condition:** Developing Sell — warning signal, NOT a hard exit
- **Action:** Tighten stop. Cut on Sell confirmation.
- **Watch for:** Downgrade to Sell in next 1–3 sessions

---

## Position Management Signals

### AddSh / Add
- **Condition:** Existing position getting add signal in confirmed uptrend
- **Action:** Add to position (momentum re-accelerating)
- **Prerequisite:** Must already hold the name

### Hold
- **Condition:** Default state — no action required
- **Frequency:** ~90% of rows on any given day

---

## MoM Thresholds

| Threshold | Interpretation | Action |
|-----------|---------------|--------|
| MoM +8 to +10 | Consideration zone | Watch for pP. Do NOT exit on MoM alone. |
| MoM > +10 held 2+ sessions with flat price | Pre-pP pattern | Expect pP signal soon |
| MoM +5 to +8 | Healthy uptrend | Hold, no action |
| MoM 0 to +5 | Early/moderate bullish | Hold, monitor |
| MoM −3 to 0 | Neutral to early bearish | Monitor for dSell |
| MoM < −7 with spBuy | Capitulation opportunity | Entry point for spBuy strategy |

**Velocity matters:** MoM acceleration (Δ per session) is as informative as absolute level. Rising MoM from +2 to +6 is more bullish than flat MoM at +8.

---

## R Thresholds

| Range | Rating | Notes |
|-------|--------|-------|
| R > +1.5 | Elite outperformer | Strongest relative strength |
| R +1.0 to +1.5 | Strong | Outperforming SPX meaningfully |
| R +0.5 to +1.0 | Good | Moderate outperformance |
| R 0 to +0.5 | Market-like | Tracking SPX |
| R < 0 | Laggard | Underperforming SPX |

**CRITICAL:** R is ONE input, not the whole quality assessment. Negative-R entries can outperform when:
- Fresh mega-cap flip with long weekly compression
- Index-flow / passive-flow exposure (lockout rally scenario)
- Regime-change or catch-up trade thesis
- Setup structure and timing trump R in these cases
