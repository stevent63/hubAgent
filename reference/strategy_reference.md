# Reversal Levels (RL) System — Strategy Reference

The canonical deep reference for the RL system. For a briefer orientation, see `context/CONTEXT.md`.

---

## Core Principle

**Bullish above RevL (Reversal Level), bearish below RevL.** Every name has a RevL that acts as a hard line. Price above RevL = bullish setup. Price below RevL = bearish setup. No exceptions.

---

## Signal Types

### Entry Signals

| Signal | Description | Conviction | Typical Mode |
|--------|-------------|------------|--------------|
| **Buy** | Price crossed RevL with confirming momentum | High | Bear-Bull Flip, Dark Green |
| **dBuy** | Developing Buy — earlier stage than Buy | Medium | Light Green, Bear-Bull (LR-LG) |
| **spBuy** | Special Buy — bottom-fishing in deep Dark Red | High risk/reward | Dark Red |
| **spBuy+** | Stronger spBuy variant | Higher conviction | Dark Red |
| **spBuy++** | Strongest bottom signal in the system | Highest bottom conviction | Dark Red |
| **wBuy** | Weak Buy — marginal signal | Lowest entry conviction | Varies |

### Exit Signals

| Signal | Description | Action |
|--------|-------------|--------|
| **Sell** | Price broke below RevL | **HARD EXIT** — no hesitation, no averaging down |
| **pP** | Profit-consideration — extended momentum is maturing | Take profits on winners. Discretion allowed. |
| **pP+** | Stronger pP variant | Higher urgency to take profits |
| **dSell** | Developing Sell — warning, not hard exit | Tighten stop, cut on Sell confirmation |

### Position Management Signals

| Signal | Description |
|--------|-------------|
| **AddSh / Add** | Add to existing position — confirmed uptrend re-accelerating |
| **Hold** | Default state — no action required |

---

## Mode Colors

Modes are extracted from CSS classes on the HTML `<td>` elements, not from text content.

| Mode | CSS Class | Meaning |
|------|-----------|---------|
| **Dark Green** | c4 | Strongest bullish — confirmed uptrend |
| **Light Green** | c5 | Bullish but weakening, or early in transition |
| **Light Red** | c7 | Bearish but weakening, or early in transition |
| **Dark Red** | c6 | Strongest bearish — confirmed downtrend |
| **Bear-Bull Flip** | c20 | Just crossed from bear to bull (fresh flip) |
| **Bear-Bull (LR-LG)** | c21 | Light Red to Light Green transition variant |

**Bullish modes:** Dark Green, Light Green, Bear-Bull Flip, Bear-Bull (LR-LG)
**Bearish modes:** Light Red, Dark Red

---

## MoM (Momentum) Scale

Range: −10 to +10

| Range | Interpretation |
|-------|---------------|
| MoM > +8 | **Consideration zone** — watch for pP signals, NOT an exit trigger by itself |
| MoM > +10 held 2+ sessions with flat price | Pre-pP pattern — expect pP soon |
| MoM +5 to +8 | Healthy uptrend momentum |
| MoM 0 to +5 | Early/moderate bullish momentum |
| MoM −3 to 0 | Neutral/early bearish |
| MoM < −7 with spBuy | **Capitulation buying opportunity** |

**Critical:** MoM velocity (Δ per session) matters as much as absolute level. Accelerating MoM is more bullish than high-but-flat MoM.

**pP timing:** The pP signal typically fires BEFORE MoM hits 10. Example: ETR fired pP at MoM +8.89, not at +10.

---

## R Value (Relative Performance vs SPX)

Trailing-window relative strength against S&P 500.

| Range | Rating |
|-------|--------|
| R > +1.5 | Elite outperformer |
| R +1.0 to +1.5 | Strong |
| R +0.5 to +1.0 | Good |
| R 0 to +0.5 | Market-like |
| R < 0 | Laggard |

**CRITICAL:** Do NOT over-index on R alone. In specific setups, structure matters more than R:
- Fresh mega-cap flips with long weekly compression and index-flow exposure
- Switch candidates with weekly mode transition
- Path 3 lockout rally scenarios where passive flows don't discriminate
- Negative-R buy signals can outperform (AMZN: R −0.42 at flip → MoM +8.48 in 5 days)

---

## Strategies

### 1. Switch Strategy
- **Entry:** Daily Buy converting to weekly hold when name transitions to double green (daily DG + weekly DG)
- **Hold period:** 3–9 months
- **Universe:** 300+ candidates post-correction
- **Exit:** Weekly mode deterioration, NOT daily
- **Allocation:** Typically 40% of fresh cash into 25–35 Switch positions
- **Distinct from:** Tactical Buy — different horizon, sizing, exit framework

### 2. Opportunist Strategy
- **Formula:** `Opportunist = Close − ((Close − RevL) × 0.6)`
- **Purpose:** Limit orders at pullback levels in confirmed uptrends
- **Use case:** Adding to existing winners on dips

### 3. spBuy Strategy
- **Entry:** Bottom-fishing on deep-bear names giving spBuy signals during capitulation
- **Risk/reward:** High
- **Sizing:** 3–5% max per name
- **Signal:** spBuy count crossing 10% of universe = capitulation threshold

### 4. MoM Swing Trading
- **Entry:** Early MoM confirmation
- **Exit:** pP signal or MoM velocity exhaustion
- **Framework:** The tactical Buy entry playbook

### 5. QuickTarget (QT) Levels
- **Formula:** `QT = Close − ((Close − RevL) × 0.4)`
- **Purpose:** Tactical pullback entry on fresh flips
- **vs Opportunist:** Less aggressive, higher fill probability

---

## Key Indicators

| Indicator | Description |
|-----------|-------------|
| **PuLL** | Medium-term strength indicator |
| **Envelope** | Price channel around RevL |
| **Iceberg charts** | Volume-based accumulation patterns |
| **Rela** | Relative strength vs SPX (weekly cadence) |
| **Key Prices** | Algorithmic support/resistance levels |

---

## Daily vs Weekly File Differences

| Field | Daily | Weekly |
|-------|-------|--------|
| Duration column | "Days" | "Weeks" |
| RevL header | "RevL" | "RevL (W)" |
| MoM header | "MoM" | "MoM (W)" |
| R-value flips | Tactical signals | Sector rotation indicators |
| Mode transitions | Entry/exit triggers | Switch triggers |

Auto-detect from column headers. Weekly has "Weeks" in header row → `file_type = 'weekly'`.

---

## Key Learnings (Validated Feb–Apr 2026 Cycle)

1. **Capitulation signal:** spBuy count crossing 10% of universe. Hit March 11–14, 2026.

2. **Recovery confirmation:** spBuy count drops to 50% of peak (~250 from ~519 peak). Hit ~March 24.

3. **Conviction framework:** Expectancy > raw hit rate. Enforce minimum sample sizes.

4. **Weekly R-value flips** are high-signal sector rotation indicators. 49 weekly R-flips into energy (mid-March) = early energy leadership signal.

5. **MoM +8 to +10 is consideration zone, not hard exit.** Wait for pP, MoM deceleration, or mode change.

6. **Negative-R buy signals should be surfaced and analyzed.** Don't filter to only positive-R.

7. **Convergence trades:** High R + bearish mode = statistical anomaly that resolves. Six convergence names all flipped April 9.

8. **Sector leader test:** If only one name in a sector is bullish, watch for followers.

9. **Energy rotation sequence:** Refiners → E&P → midstream → majors selling.

10. **Mining broadening wave:** Copper/aluminum/gold → silver → steel → PGMs → juniors → rare earths → uranium.

11. **Path-dependent framework:** Market scenarios (chop, pullback, lockout rally) should inform deployment, not just R quality.

12. **Switch framework:** Post-correction with 300+ candidates is the best Switch setup in 2+ years. Distinct allocation and exit framework from tactical.
