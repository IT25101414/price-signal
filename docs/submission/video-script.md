# Three-minute demonstration script

Record this only after the public URL, buyer-feedback result and final report are updated. Use the public build on real data. Keep a clock visible while rehearsing; target 2:45 to 2:55.

## 0:00–0:20 — problem and user

**Show:** Welcome page and independent-project notice.

**Say:** “Price Signal is for small food buyers in Colombo who see today’s price but cannot easily judge whether a move at Dambulla is likely to reach Pettah or Narahenpita. It turns the Central Bank’s daily price reports into a cautious three-report-day signal. This is an independent student project, not Central Bank advice.”

## 0:20–0:45 — real data and freshness

**Show:** Today page, source status and report date.

**Say:** “The collector follows robots.txt and its ten-second delay, records every downloaded file and rejects report layouts it does not recognise. These cards are built from the report dated [FINAL DATA DATE]. The guard checks freshness again on every page request.”

## 0:45–1:25 — one useful signal

**Show:** Filter to one `ok` card; point to Dambulla price, Colombo price, expected change and 80% range.

**Say:** “For this item, the model compares the current Dambulla-to-Colombo gap with its usual gap and estimates how much may close over the next three report days. The range is intentionally prominent because the effect is uncertain. The model does not say buy or sell; it is one input for deciding whether to buy now, split a purchase or wait.”

## 1:25–1:50 — evidence, not decoration

**Show:** Method page.

**Say:** “On data from 2024 onward, adding Dambulla removed about six to twelve percentage points of squared forecast error beyond the price’s own history. A placebo showed almost nothing. The stated 80 percent range covered 77.4 to 81.5 percent of unseen three-day outcomes. In simulation, the model cost 1.2 to 1.6 percent less than always buying today, but this is not observed buyer savings.”

## 1:50–2:20 — fail safely

**Show:** a no-clear-signal card, then prepared stale-data screenshot or safe local test build.

**Say:** “Knowing when not to speak is part of the product. With a small gap, missing market price, closed market, unread newer report or data more than three working days old, the server removes the numbers and explains why. Twelve deliberate refusal cases pass, and the website tests check that withheld values do not leak through its APIs.”

## 2:20–2:40 — history and report

**Show:** Explore, change the item and time range; then Weekly report.

**Say:** “The buyer can compare past Dambulla and Colombo prices, inspect their gap, and download a guarded weekly comparison. History is hidden under the same freshness rules.”

## 2:40–3:00 — honest close

**Show:** Help page or README and final commit.

**Say:** “The pipeline, model and six-page site are reproducible from the public repository. Eighty-four automated tests pass without environment-dependent skips, and the code, permission evidence, MIT licence and AI-use disclosure are public. [ONE SENTENCE WITH REAL BUYER RESULT, OR: ‘Real buyer feedback remains a limitation and is not claimed.’] The key result is a modest, tested Dambulla lead presented with uncertainty and safe refusal.”

## Before recording

- Replace `[FINAL DATA DATE]` and the buyer-feedback sentence with verified facts.
- Warm the public service, close unrelated tabs and increase browser zoom so labels are readable.
- Do not show a terminal containing local paths, email addresses or tokens.
- Record one continuous successful run on the exact submitted commit.
