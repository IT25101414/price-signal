# Private-browser submission check

Run this only after the public site and video exist. Record the date, browser and result beside each item.

- [ ] Open the GitHub repository while signed out; the README and files are visible.
- [ ] Follow the website link from the top of the README; no login is required.
- [ ] Wait through a free-host cold start if needed, then reload once.
- [ ] Open `/healthz`; it returns `{"ok": true}`.
- [ ] Open `/api/status`; record `state`, `report_date` and `newest_listed`.
- [ ] Welcome, Today, Explore, Weekly report, Method and Help all load.
- [ ] Today shows a report date and either safe estimates or a plain refusal reason.
- [ ] Explore and Weekly report do not expose history when the guard refuses.
- [ ] Check a 390 px-wide viewport for horizontal page overflow.
- [ ] Download the CSV; confirm it contains only figures the page is allowed to show.
- [ ] Open the technical report and two-page summary from the submitted links.
- [ ] Play the complete video while signed out; confirm sound, text and the three-minute limit.
- [ ] Confirm the report, summary, README, video and live site all name the same commit/build and data date.
- [ ] Confirm CBSL attribution, non-endorsement and AI-use disclosures are visible.
- [ ] Confirm no private email address, local file path, secret or raw report archive is published.

Final rehearsal result: **pending public deployment and video**.
