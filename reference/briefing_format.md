# Morning Briefing Format — Non-Negotiable

This format is not a stylistic preference. It has been reinforced across multiple sessions and is the required structure for every morning briefing.

---

## Section 1: What Changed Overnight

Always the first section. Always.

- X new Buy | Y new Sell/pP | Z bear→bull | W bull→bear (equity subset)
- Mode distribution table (yesterday vs today with deltas)
- Bullish % change
- spBuy count change (capitulation / recovery indicator)

## Section 2: Portfolio Signals

If the user has active positions, report portfolio-specific events:

- New exits (Sell, pP, pP+) — execute immediately
- New warnings (dSell) — tighten stops
- Names entering consideration zone (MoM >= 8)
- Biggest MoM accelerators in portfolio
- Active count change

## Section 3: Conviction Ideas

- Lead with 2–3 highest conviction calls
- Direct language, no hedging — conviction is value-add
- Signal priority order:
  1. Buy
  2. dBuy
  3. spBuy
  4. Trend changes (bear→bull flips)
  5. Switch candidates
  6. MoM > 7
  7. R flips
- Cluster by sector/theme, NOT ticker-alphabetic, NOT by R value

## Section 4: Macro/Sector Context

- Index ETF status (SPY, QQQ, IWM, DIA)
- Sector ETF changes (XLE, XLK, XLF, etc.)
- Bond/commodity context if relevant
- External context seasons signals — it does NOT override them

## Section 5: Playbook

- Numbered actions for the day
- Specific price levels, not vague guidance
- Exit instructions for triggered signals
- Watch list for next 1–3 sessions

---

## Tone Rules

- **High signal per word.** Chris reads fast, values density, doesn't need padding.
- **No padding, no caveats** unless the caveat is material to the trade.
- **Conviction is value-add.** Going on a limb when signals support it is the job, not the risk.
- **External context seasons signals, doesn't override them.** If signals contradict headlines, trust signals and say so.
- **No hedging language.** "Might consider potentially looking at" → "Buy CENX at open."

---

## Data Sources

For each morning briefing, a Claude session needs:

1. `parsed_csv/{today}_daily.csv` — today's full signal data
2. `parsed_csv/{yesterday}_daily.csv` — prior session for diff
3. `analyses/{today}_diff.md` — pre-computed overnight diff
4. `context/CONTEXT.md` — system orientation
5. `master/portfolio_ledger.csv` — current positions (optional but recommended)
