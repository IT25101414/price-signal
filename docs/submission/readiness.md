# Implementation submission readiness

Checked 18 October 2026 against the ModelX 2.0 implementation requirements. This file separates completed evidence from work that needs a real participant, the repository owner or a public service.

| Requirement | State | Evidence / exact next action |
|---|---|---|
| Functionality frozen | Complete | `v1.0.0-rc1`; `docs/functionality-freeze-2026-10-17.md` |
| Automated verification | Complete | 85 passed with no environment-dependent skips; 12/12 refusal cases and all three model self-tests passed. Original-report validation is an explicit local evidence check. |
| Real-data end-to-end product | Complete locally | Committed cards dated 15 Oct 2026; Welcome, Today, Explore, Weekly report, Method and Help pages |
| Data-use evidence | Complete | Redacted CBSL reply in `docs/cbsl_reply_2026-10-12.pdf`; attribution and non-endorsement wording included |
| Buyer-feedback materials | Complete | Session guide and response template in `docs/buyer-feedback/` |
| Real buyer feedback | Complete | Three consented anonymous sessions on 16-17 Oct; task counts, individual ratings, medians, decisions and limitations are in `findings-summary.md` |
| Public hosting | Technically prepared | `render.yaml` and `web/DEPLOY.md` are ready; the repository owner must sign in to Render, connect GitHub and approve service creation |
| README run instructions | Complete | Root README plus `web/README.md`; public URL must be added after deployment |
| Open-source licence | Complete | Repository owner selected and committed the MIT License on 18 Oct 2026; third-party data and emblem exclusions are stated in the README |
| Technical report | Source updated; final PDF pending URL | Buyer results and resulting changes are in `technical-report.md`; regenerate the reviewed PDF after adding the verified public URL |
| Two-page summary | Submission-ready draft | Buyer result is included; add the verified public URL if the submission format requires it |
| Three-minute video | Script ready | Buyer result is included; record after deployment so the video matches the submitted build |
| Private-browser rehearsal | Pending deployment/video | Open repository, website and video without an authenticated session; follow `docs/submission/private-browser-check.md` |

## Release rule

Do not replace the pending public URL with a guessed address. After any functionality change, repeat the freeze checks before recording the video.
