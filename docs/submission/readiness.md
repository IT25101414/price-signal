# Implementation submission readiness

Checked 18 October 2026 against the ModelX 2.0 implementation requirements. This file separates completed evidence from work that needs a real participant, the repository owner or a public service.

| Requirement | State | Evidence / exact next action |
|---|---|---|
| Functionality frozen | Complete | `v1.0.0-rc1`; `docs/functionality-freeze-2026-10-17.md` |
| Automated verification | Complete | 86 passed with no environment-dependent skips; 12/12 refusal cases and all three model self-tests passed. Original-report validation is an explicit local evidence check. |
| Rolling-time stress test | Complete | Three non-overlapping 2026 test windows; 9/9 Dambulla gains positive, 9/9 wrong-item placebos non-positive; `results_rolling_stress.txt` |
| Accessibility audit | Complete for automated scope | Six source pages and principal light/dark contrast pairs pass; rendered browser structure also checked; `results_accessibility.txt` |
| Phase 1 proposal | Complete and reviewed | Every required proposal section is substantively answered; final PDF is `phase1-project-proposal.pdf` |
| Real-data end-to-end product | Complete locally | Committed cards dated 15 Oct 2026; Welcome, Today, Explore, Weekly report, How it works and Help pages |
| Data-use evidence | Complete | Redacted CBSL reply in `docs/cbsl_reply_2026-10-12.pdf`; attribution and non-endorsement wording included |
| Buyer-feedback materials | Complete | Session guide, three anonymised response records and the findings summary are in `docs/buyer-feedback/` |
| Real buyer feedback | Complete | Three consented anonymous sessions on 16-17 Oct; task counts, individual ratings, medians, decisions and limitations are in `findings-summary.md` |
| Revised-wording buyer retest | Prepared, real sessions pending | Use `docs/buyer-feedback/retest-guide.md` with one or two buyers after deployment; do not invent outcomes |
| Public hosting | Technically prepared | `render.yaml` and `web/DEPLOY.md` are ready; the repository owner must sign in to Render, connect GitHub and approve service creation |
| Public smoke monitor | Implemented, URL activation pending | `web/smoke_test.py` passes locally; set the `PUBLIC_SITE_URL` GitHub variable after deployment to enable the weekday workflow |
| README run instructions | Complete | Root README plus `web/README.md`; public URL must be added after deployment |
| Open-source licence | Complete | Repository owner selected and committed the MIT License on 18 Oct 2026; third-party data and emblem exclusions are stated in the README |
| Technical report | Complete for the verified local release | Clean PDF regenerated from the current source with buyer results, rolling evidence, 86-test result, accessibility evidence and licence state; add the verified public URL after deployment |
| Two-page summary | Complete for the verified local release | Reviewed two-page PDF includes the buyer result, rolling evidence and safety checks; add the verified public URL after deployment |
| Three-minute video | Script ready | Buyer result is included; record after deployment so the video matches the submitted build |
| Private-browser rehearsal | Pending deployment/video | Open repository, website and video without an authenticated session; follow `docs/submission/private-browser-check.md` |

## Release rule

Do not replace the pending public URL with a guessed address. After any functionality change, repeat the freeze checks before recording the video.
