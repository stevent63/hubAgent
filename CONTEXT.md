# CONTEXT.md
## hubAgent — Reversal Levels Trading Analysis System

**Last updated:** April 14, 2026
**Purpose:** Orient any Claude session (web chat, CLI, future instance) to the user, system, and current state. Read this first before doing any work.

---

## Who You're Working With

**Chris** — active trader since 2015, using the Reversal Levels (RL) system daily. Fort Lauderdale, FL. Primary platform: Reversal Levels. Primary broker context: active daily trader, runs multiple strategies simultaneously. Technical enough to run Claude Code CLI, Python pipelines, and Polygon API; not a software engineer by trade.

**Communication preferences:**
- Direct, no-hedging analysis
- Conviction calls are VALUE-ADD, not risk — Chris explicitly wants you to go on a limb when signals support it
- Narrative/story context enhances signal reads; it shouldn't OVERRIDE signal reads
- When signals contradict external headlines, trust signals and say so
- Do NOT over-index on any single metric (R value is one input, not the whole quality assessment)
- Path-dependent thinking matters — frame analysis around scenarios (chop/pullback/lockout rally), not single outcomes
- Feedback loop tight — Chris will push back when reasoning is thin or frameworks are misapplied, and that pushback is valid

---

## The Reversal Levels (RL) System — Fundamentals

**Core rule:** Bullish above RevL (Reversal Level), bearish below RevL. Every name has a RevL that acts as a hard line.

**Signal types (exit and entry signals, not just Buy/Sell):**
- **Buy** — price crossed RevL with confirming momentum; entry signal
- **dBuy** — developing Buy, earlier stage than Buy
- **spBuy / spBuy+ / spBuy++** — special Buy / bottom-fishing signals when a name is deep in Dark Red; the ++ is highest conviction bottom signal
- **wBuy** — weak Buy
- **Sell** — price broke below RevL; exit signal (hard)
- **dSell** — developing Sell; warning, not hard exit yet
- **pP / pP+** — profit-consideration signal on extended momentum; the system saying "this winner is mature, consider taking profits"
- **AddSh / Add** — add-to-position signals on existing holdings
- **Hold** — the default state; no action required

**Mode colors (visualized in RL dashboards via CSS classes):**
- **Dark Green (c4)** — strongest bullish mode; confirmed uptrend
- **Light Green (c5)** — bullish but weakening OR early in transition
- **Light Red (c7)** — bearish but weakening OR early in transition
- **Dark Red (c6)** — strongest bearish mode; confirmed downtrend
- **Bear-Bull Flip (c20)** — just crossed from bear to bull (fresh flip)
- **Bear-Bull LR-LG (c21)** — Light Red to Light Green transition variant

**Momentum (MoM) scale:** −10 to +10.
- MoM > +8 is the "consideration zone" — watch for pP signals, not an exit trigger by itself
- MoM > +10 or MoM 10.0 held for multiple sessions with decelerating price is the pre-exit pattern
- MoM < −7 in Dark Red with spBuy signal = capitulation buying opportunity
- Path-dependent: MoM velocity (Δ per session) matters as much as absolute level

**R value** — relative performance vs SPX on a trailing window.
- R > +1.5 = elite outperformer
- R > +1.0 = strong
- R 0 to +0.5 = market-like
- R < 0 = laggard (relevant for regime-change bets and catch-up trades, NOT inherently disqualifying)

**CRITICAL:** Do not over-index on R alone. In some setups (fresh mega-cap flips, Switch candidates, Path 3 lockout rallies), setup structure matters more than R. A Day 1 flip with long weekly compression and mega-cap index-flow exposure can be a better entry than a Day 21 name with R +2.0 that already ran.

---

## Strategies Chris Uses

1. **Switch Strategy** — Daily entry converting to weekly hold when a name transitions to double green (daily DG + weekly DG). Long-term trend reversal bet. Hold 3-9 months. Larger universe (300+ candidates at any given time post-correction). Exit on weekly mode deterioration, not daily.

2. **Opportunist Strategy** — Limit orders at computed pullback levels in confirmed uptrends. Formula: `Opportunist = Close − ((Close − RevL) × 0.6)`. For adding to existing winners on dips.

3. **spBuy Strategy** — Bottom-fishing on deep-bear names giving spBuy signals during capitulation. Higher risk/reward. Sized smaller (3-5% max per name).

4. **MoM Swing Trading** — Entry on early-MoM confirmation, exit on pP signal or MoM velocity exhaustion. The tactical Buy entry playbook.

5. **QuickTarget Levels** — Formula: `QT = Close − ((Close − RevL) × 0.4)`. Used as tactical pullback entry on fresh flips. Less aggressive than Opportunist; higher fill probability.

**Important:** These strategies are NOT interchangeable. Each has different horizon, sizing, exit framework. Switch != Buy != spBuy.

---

## Key Indicators Beyond Mode/Signal/MoM/R

- **PuLL** — medium-term strength indicator
- **Envelope** — price channel around RevL
- **Iceberg charts** — volume-based accumulation
- **Rela** — relative strength vs SPX (weekly cadence)
- **Key Prices** — algorithmic support/resistance levels
- **Weekly vs Daily** — weekly file has different columns ("Weeks" not "Days"), different headers ("RevL (W)" not "RevL"). The R-value flips happen at the WEEKLY level (49 weekly R-flips into energy was an early-cycle signal). Weekly mode transitions are Switch triggers.

---

## HTML Column Mapping (for extract.py)

Daily file table structure:
- Index 0: Name
- Index 1: Ticker
- Index 2: Close
- Index 3: Tr (weekly trend weeks)
- Index 4: Mode (via CSS class on the cell)
- Index 5: RevL
- Index 6: MoM
- Index 7: Days (in current mode)
- Index 8: P/L%
- Index 10: R value

CSS class to mode mapping:
- c4 → Dark Green
- c5 → Light Green
- c6 → Dark Red
- c7 → Light Red
- c20 → Bear-Bull Flip
- c21 → Bear-Bull (LR-LG)

Weekly file differs: "Weeks" instead of "Days" column, "RevL (W)" / "MoM (W)" headers. Auto-detect from column names.

Deduplication: RL HTML sometimes has duplicate rows. Dedupe by (name + ticker + signal_type) compound key.

---

## The Morning Briefing Format — NON-NEGOTIABLE

Every morning briefing follows this structure. This is not a stylistic preference; Chris has reinforced it multiple times.

1. **"What Changed Overnight"** — first section, every time
   - New Buy count / new Sell count / bear→bull flips / bull→bear flips
   - Mode distribution change (DG/LG/LR/DR counts + bullish%)
   - spBuy count change (capitulation / recovery indicator)

2. **Signal priority order** (when narrating new entries):
   - Buy → dBuy → spBuy → trend changes → Switch candidates → MoM >7 → R flips

3. **Cluster by sector/theme** — not ticker-alphabetic, not by R value

4. **Lead with 2-3 highest conviction ideas** — direct conviction calls, no hedging language

5. **Portfolio status section** — active count, new exits, new warnings (dSell), names entering consideration zone, biggest MoM accelerators

6. **Playbook at the end** — numbered actions for the day

---

## Portfolio Philosophy

- **Position count target:** ~50-65 active positions during deployment phases
- **Sizing framework:** Core 5-8%, Conviction 3-4%, Asymmetric/Speculative 1.5-2%
- **Diversification:** Across themes (semi, mining, biotech, satellite, energy, industrial, etc.), not just names
- **Exit discipline:** Trust the system. Sell = exit. pP = consider exit (take profits on winners). dSell = warning, tighten stop. Don't front-run exits; don't delay confirmed exits.
- **Management vs deployment modes:** When market is broadly bullish and portfolio is diversified, the work shifts from "find new entries" to "execute profit-takes on extended winners."

---

## Key Learnings Compounded Across The Cycle

These are patterns validated by real execution during the Feb 28 – Apr 14, 2026 correction and recovery:

1. **Capitulation signal:** spBuy count crossing 10% of universe is the key threshold. Was hit March 11-14, 2026.

2. **Recovery confirmation:** When spBuy count drops to 50% of peak (~250 from ~519 peak), the recovery is confirmed. Was hit ~March 24.

3. **Conviction framework:** Expectancy > raw hit rate. Enforce minimum sample sizes before reporting rates. Don't generalize from 3 trades.

4. **R-value flips on weekly cadence** are high-signal sector rotation indicators. 49 weekly R-flips into energy in mid-March was an early indicator of the energy leadership that played out for 3 weeks.

5. **MoM +8 to +10 is profit-CONSIDERATION zone, not hard exit.** Wait for pP signal, MoM deceleration, or mode change as actual exit triggers. The pP typically fires BEFORE MoM hits 10 (e.g., ETR fired pP at +8.89, not +10).

6. **Negative-R buy signals should be surfaced and analyzed.** Don't filter to only positive-R names. AMZN flipped with R -0.42 and ran to MoM +8.48 in 5 days (April 9→14). MELI flipped with R -0.74 and is now a successful position. The R-skeptic framework was validated.

7. **Convergence trades:** High R + bearish mode = statistical anomaly that resolves. On April 9, six convergence names (VICR, MU, COHR, AMAT, LRCX, ASML) all flipped bullish in one session after being identified April 3.

8. **Sector leader test:** If only one name in a sector is bullish among many peers, watch for followers. CAT was solo bullish industrial April 3; by April 9 the entire industrial complex followed (DE, PH, CMI, ETN, PWR, DD, FDX, UNP).

9. **Energy rotation sequence:** refiners (CLMT, PARR) → E&P (OXY, COP, EOG) → midstream (WMB, TRP, OKE) → majors selling (CVX, XOM, PSX, PBF). Full cycle played out Feb-Apr 2026.

10. **Mining broadening wave:** Copper/aluminum/gold leaders (FCX, CENX, AA, NEM) flip first → silver (SSRM, PAAS, SVM) → steel (MT) → PGMs (SBSW, PPLT) → juniors (SILJ) → rare earths (REMX) → uranium (URNM). Pattern repeats across cycles.

11. **Path-dependent framework added April 13.** Market scenarios: chop/laggards catch up, pullback higher low, lockout rally grind up. Fresh cash deployment should consider WHICH PATH wins, not just R quality. Lockout rallies punish R-based filtering because passive flows don't discriminate.

12. **Switch framework under-applied April 4-13.** Recognized April 14: post-correction environment with 300+ Switch candidates is the best Switch setup in 2+ years. Switch is distinct from tactical Buy and needs its own allocation (typical: 40% of fresh cash into 25-35 Switch positions, hold 3-9 months, different exit framework than tactical).

---

## System Architecture — Current State (April 14, 2026)

**What exists:**
- Python extraction pipeline (BeautifulSoup) — parses RL HTML to JSON
- Diff engine — computes overnight changes vs prior session
- Morning briefing template — proven format, reproducible
- Multiple skill files in `/mnt/skills/user/` — EOD reconciliation, hit-rate tracker, weekend analyst, switch viz, etc.
- Polygon API key available (not yet integrated due to web chat network restrictions)
- Portfolio of 52-55 active positions (changes daily as pP signals fire)

**What's missing / being built:**
- **Persistent data layer** — This repo (`hubAgent`) is the solution
- **Historical RL signal database** — master_history.csv accumulated across sessions
- **Position ledger** — portfolio_ledger.csv tracking entries/exits with P/L
- **Weekly file parser** — extractor needs update for weekly column structure
- **EOD reconciliation deployment** — designed, Polygon key available, needs CLI execution
- **Hit-rate tracker** — Saturday analytical run, needs historical data to be meaningful
- **Sector classification map** — static ticker→sector CSV to automate theme clustering

**What's been explicitly solved:**
- Morning briefing format (non-negotiable, documented here)
- RL signal priority order
- Portfolio sizing framework
- Exit discipline (trust the system, no front-running, no delay)
- Path-dependent portfolio construction (added April 12)

---

## Current Portfolio (as of April 14, 2026 close — approximate)

**Active positions: ~52** (after pP exits on FCX, HBM, SCCO on April 14)

**Recent exits (last 3 sessions):**
- April 14: FCX (+11.98%), HBM (+18.61%), SCCO (+15.56%) — all pP, mining theme maturing
- April 13: ETR (+4.42%), KOD (+2.91%) — both pP
- April 10: HCC (+0.34%, Sell), ETR (+5.29%, pP — re-entry on bounce), GH (-9.48%, Sell)
- April 8: AXGN (+4.2%, Sell)

**Consideration zone (MoM ≥ 8, April 14 close):**
INTC (+10.0), POWL (+8.84), FORM (+8.64), GLW (+8.50), STX (+8.47), CENX (+8.37), SNDK (+8.22), SSRM (+8.21), TER (+8.20), ASX (+8.14), AMD (+8.05) — expect sequential pP over coming sessions

**dSell warnings (April 14):** EIX, NEE, ATO (utility theme weakening), SPHR

**Still holding strong (core):** PRAX, ARWR, CIEN (optical), NEM/RGLD (gold), KYMR, BBIO, APGE, EWTX, XBI (biotech), POWL, VRT-adjacent (power infra), GS, CAT, INTC (until pP), SNDK, TER, FORM, MKSI, AEIS (semi)

**FRO** — last energy-adjacent name. XLE in Dark Red. Monitor for any deterioration → immediate exit.

---

## Open Items / In Progress

1. **Weekly file extractor broken** — column parsing returns "Unknown" mode and zero R for all names. Fix needed in extract.py (weekly has different CSS classes or column order).

2. **Persistent data layer migration** — THIS repo project. Get `hubAgent` operational with extract, diff, portfolio_track, signal_search.

3. **Switch universe analysis** — 58-name list analyzed April 14 structurally; needs actual signal data once extractor is fixed and master_history is populated. Top Switch candidates identified: V, MA, AXP, UNH, TMO, BLK, BKNG, ORLY, SWKS.

4. **EOD reconciliation deployment** — script designed, Polygon key available (`AEAnWuVQl33zGCnt1FtIUeaml3obF0dx`), needs CLI environment to run because web chat container can't reach api.polygon.io.

5. **Skills migration** — copy `/mnt/skills/user/` skill files into `hubAgent/skills/` for versioned persistence.

6. **Reference PDFs** — 13 RL strategy PDFs should live in `hubAgent/reference/pdfs/`.

7. **QuickTarget multiplier confirmation** — Chris has not yet confirmed whether his RL platform QT multipliers match the 0.4/0.6 defaults used in calculations. Minor, verify when convenient.

---

## How To Start A New Claude Session

Paste at the start of any new conversation:

```
Read the following files before we begin:
- https://raw.githubusercontent.com/stevent63/hubAgent/main/context/CONTEXT.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/reference/briefing_format.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/reference/strategy_reference.md

Today's RL file is at:
https://raw.githubusercontent.com/stevent63/hubAgent/main/parsed_csv/YYYY-MM-DD_daily.csv

Prior session is at:
https://raw.githubusercontent.com/stevent63/hubAgent/main/parsed_csv/YYYY-MM-DD_daily.csv

Run the morning briefing.
```

That's the bootstrapping pattern. Any Claude session — fresh or continuation — is operational in 30 seconds. This is the architectural goal.

---

## Core Principles (Repeat When Uncertain)

1. **Signals first, narrative second.** Report what the data says; layer context to explain, not override.
2. **Conviction is value-add.** Going on a limb when signals support it is the job, not the risk.
3. **Trust the system's exit signals.** No front-running, no delay, no averaging down.
4. **Path-dependent thinking.** Most analyses should address multiple market scenarios.
5. **R is an input, not the answer.** Setup structure, timing, theme context, index flows all matter.
6. **Compound analysis across sessions.** Persistent memory is the goal; ephemeral insight is the failure mode.
7. **High signal per word.** Chris reads fast, values density, doesn't need padding.