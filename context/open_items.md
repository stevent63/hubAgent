# Open Items / In Progress

Tracked from CONTEXT.md and build spec. Updated as phases complete.

---

1. **Weekly file extractor fix** — column parsing returns "Unknown" mode and zero R for all weekly names. Requires extract.py update for weekly column structure/CSS classes.
   **Status:** [NOT STARTED]

2. **Persistent data layer migration** — hubAgent repo as the durable data layer for RL signal history, portfolio tracking, and analysis outputs.
   **Status:** [IN PROGRESS — Phases 1-3b complete]

3. **Switch universe analysis tracking** — 58-name Switch candidate list needs signal data once extractor is fixed and master_history is populated. Top candidates: V, MA, AXP, UNH, TMO, BLK, BKNG, ORLY, SWKS.
   **Status:** [NOT STARTED]

4. **EOD reconciliation deployment** — script designed, Polygon key available, needs CLI environment to execute.
   **Status:** [DEFERRED — Phase 5]

5. **Skills migration** — copy skill files into hubAgent/skills/ for versioned persistence.
   **Status:** [DONE — Phase 4a, 6 skills migrated]

6. **Reference PDFs** — 12 RL strategy PDFs in hubAgent/reference/pdfs/.
   **Status:** [DONE — Phase 4a, 12 PDFs migrated]

7. **QuickTarget multiplier verification** — confirm whether RL platform QT multipliers match the 0.4/0.6 defaults used in calculations.
   **Status:** [PENDING USER]
