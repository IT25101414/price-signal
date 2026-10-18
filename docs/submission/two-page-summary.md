# Price Signal

## A guarded early-warning view of Colombo food-price movements

**ModelX 2.0 · Economy and livelihoods · Nivetha Ramanan, SLIIT**  
**Repository:** <https://github.com/IT25101414/price-signal>  
**Public app:** `[PENDING OWNER-AUTHORISED DEPLOYMENT]`

### The problem

Small canteens, restaurants and shops in Colombo must buy food while prices move quickly. The Central Bank of Sri Lanka publishes daily market prices, but each PDF mainly says what changed since the preceding report. It does not tell a buyer whether an unusual move at Dambulla is likely to reach Pettah or Narahenpita, how much of the gap normally closes, or when the evidence is too weak to use.

### What Price Signal does

Price Signal turns the Daily Price Reports into cautious three-report-day estimates for supported foods. Each card shows the latest Dambulla and Colombo prices, how unusual their gap is, the expected Colombo change and an 80% likely range. It never says “buy” or “sell”. It is designed as one input beside stock, spoilage, urgency, transport and cash flow.

The product includes a plain-language Welcome page, a live-status Today dashboard, historical Explore charts, a guarded Weekly report, a public-facing How it works evidence page and Help. A welcome-page selector provides a persistent English, Sinhala or Tamil core experience for local users while preserving official item, market, date and source values. It runs as a small Flask/SQLite website and also has a Streamlit dashboard.

### From source to user

`CBSL reports → polite collector → position-based PDF parser → local price table → ridge model → safety guard → website`

The collector respects robots.txt and a ten-second crawl delay, downloads each file once and records its hash. The parser reads table values by position because the PDFs drop empty cells from their text layer; unfamiliar layouts are rejected, not guessed. Historical data train and test the model, while the latest accepted report controls the interface. The committed build uses the 15 October 2026 report.

The Central Bank's Statistics Department replied on 12 October 2026 that the published data are publicly available and do not require specific approval for use. It requested attribution and stated that CBSL does not endorse derived results. The repository contains a redacted copy. Raw PDFs, the complete generated table and personal data are not published.

### The delivered insight

The model asks a focused question: after accounting for a Colombo price's own recent movement, does Dambulla add useful information? On held-out 2024–2026 data, it does.

| Colombo series | Three-day gain over own history | Inside stated 80% range | Simulated cost vs buying today |
|---|---:|---:|---:|
| Wholesale Pettah | +9.7 points | 81.0% | −1.42% |
| Retail Pettah | +8.3 points | 81.5% | −1.22% |
| Retail Narahenpita | +12.1 points | 77.4% | −1.57% |

Gain is the additional share of squared forecast error removed. The placebo is approximately zero. The simulated cost result is not observed savings: it assumes a buyer can defer a purchase without shortage, spoilage or operating cost. The ranges are wide, so the interface makes uncertainty visible.

A separate rolling-origin check refitted the three-day model before three non-overlapping May–October 2026 test windows. All 9 Dambulla gains were positive (+5.5 to +13.7 points), all 9 wrong-item placebos were zero or negative, and a majority of items benefited in all 9 comparisons. This strengthens recent stability evidence but does not test the 2022 crisis.

### Safe refusal is a feature

Price Signal removes estimates when the Central Bank listing cannot be checked, a newer report has not been parsed, the latest good data are more than three working days old, a market is closed, a price is missing, recent paired history is insufficient or the gap is too small. The server applies the guard again on every request and withholds history as well as cards.

Verification on 18 October 2026: **87 reproducible tests passed with no environment-dependent skips**, **12 of 12 deliberate refusal cases passed**, and the model, robustness and decision-policy synthetic self-tests passed. The 125-value check against original CBSL reports remains a separate, explicit local validation because the source PDFs are not redistributed.

All six pages also pass a reproducible accessibility structure and principal-colour contrast check; a rendered-browser audit found no unnamed controls or broken label relationships. An 8/8 local service smoke test covers health, safety status and every page, and the same check is ready to run automatically against the public URL.

### What three buyers understood

Three anonymous, consented sessions on 16-17 October covered a restaurant, vegetable shop and hotel/catering business. Median ratings were **4/5** for main-card understanding, trust as one buying input and usefulness. Two participants needed help with the possible range, all three needed help or could not complete the history comparison, and two were unsure why weekly values were blank. The interface now explains that the tested range held about eight times in ten, replaces “paired report days” with days when both prices were available, explains the start-at-100 chart and states that a blank weekly value means a required daily price was unavailable. The revised wording has not yet been retested.

### Honest scope

The effect is modest and covers only 18–19 foods with a Dambulla wholesale price. The test period is calmer than the 2022 crisis, prices are rounded and the three-report-day horizon can cross a weekend. The buyer study has only three participants and measures comprehension and stated intent, not actual purchasing behaviour or savings. Public deployment is not yet verified, and no public URL is guessed.

### Final submission actions

1. Complete the Render deployment, verify `/healthz` and add the exact public URL.
2. Add the verified URL to the already-reviewed proposal, technical report and two-page summary PDFs.
3. Record the three-minute demonstration from the exact submitted build and complete the signed-out browser rehearsal.

**Attribution:** Daily Price Report data — Statistics Department, Central Bank of Sri Lanka. CBSL does not endorse this project, its analysis or its conclusions.  
**AI disclosure:** Claude and OpenAI Codex assisted with research, drafting, code and review; the repository's `AI_USE.md` gives the file-level account. The author reviewed the work and is responsible for the submission.
