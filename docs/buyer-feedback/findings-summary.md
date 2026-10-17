# Buyer feedback findings

Status: **three consented buyer sessions completed**. The project owner confirmed on 18 October 2026 that all three participants permitted anonymous use of their responses.

## Study record

- Session dates: 16 October 2026 (participant 1); 17 October 2026 (participants 2 and 3)
- Number of participants: 3
- Buyer types represented: small restaurant; small vegetable shop; small hotel and catering business
- Test setting and devices: not recorded in the supplied session notes
- Version tested (commit and public URL, if available): pre-deployment build available on 16-17 October; exact commit and device were not recorded
- Facilitator: not recorded in the supplied session notes
- Consent: anonymous publication confirmed for all three participants by the project owner on 18 October 2026

## Task results

| Task | Completed without help | Completed with help | Not completed | Main difficulty |
|---|---:|---:|---:|---|
| Current card | 2 | 1 | 0 | One participant needed the Dambulla-to-Colombo relationship explained |
| Estimate and likely range | 1 | 1 | 1 | The range was not understood confidently by two participants |
| No-signal state | 1 | 2 | 0 | Two initially needed help distinguishing weak evidence from no price change |
| Six-month history | 0 | 2 | 1 | Paired/shared report days and the common starting value were unclear |
| Weekly report | 1 | 2 | 0 | Two participants asked why some weekly values were blank |

## Ratings

Report the individual scores as well as the median because the sample is very small.

| Measure | Individual scores | Median |
|---|---|---:|
| Main-card understanding (1–5) | 4, 3, 4 | 4 |
| Trust as one decision input (1–5) | 4, 2, 4 | 4 |
| Usefulness for work (1–5) | 5, 3, 4 | 4 |

## Findings and decisions

| Evidence from participants | Severity | Decision/change | Verification |
|---|---|---|---|
| Two of three participants could not explain the possible range without help; one did not complete the task. | high | Explain that the range held the real change about 8 times in 10 in past testing and is not a guaranteed best/worst case; label row values as “Possible range”. | Automated copy regression passes; participant retest not yet conducted. |
| All three needed help or failed the history task; “paired report days” and the shared baseline were named explicitly. | high | Replace technical labels with “days when both prices were available” and explain that 110 means 10% above the starting price. | Automated copy regression passes; participant retest not yet conducted. |
| Two participants were unsure why weekly values were blank. | medium | State beside the chart and table that a blank means at least one of the five required daily prices was unavailable, not zero. | Automated copy regression passes; participant retest not yet conducted. |
| One participant requested a clearer latest-data date even though the date was already present in the heading. | medium | Add a dedicated “Price data [date]” status chip. | Automated copy regression passes; participant retest not yet conducted. |

Severity guide:

- `critical`: could cause an unsafe or seriously wrong interpretation; fix before deployment.
- `high`: blocks a core task for more than one participant; fix before submission.
- `medium`: causes delay or requires help; fix if time permits.
- `low`: preference or polish with little effect on task completion.

## Behaviour and value

- Participants who said they would use it as one input: 2 of 3 clearly described using it for checking or planning while still confirming the supplier price; the third might browse it but would continue relying mainly on suppliers.
- Participants who described a specific possible change in checking or buying behaviour: 2 of 3 (checking before going to market; using it when planning future purchases).
- Reasons for not using it: uncertainty about accuracy and difficulty understanding the range; continued trust in regular suppliers.
- Most useful feature: an early Dambulla-to-Colombo comparison for planning, while keeping the current supplier price as the final check.
- Most confusing feature: the possible range, followed by shared report days/common baseline and blank weekly values.

## Changes made

- Today page: clearer possible-range explanation and visible source-data date, justified by participants 1 and 2.
- Explore page: plain-language shared-date and start-at-100 explanations, justified by all three participants.
- Weekly page: explicit reason for blank values, justified by participants 2 and 3.
- Help page: glossary entries for shared report day, start-at-100 charts and blank weekly values.
- Regression coverage: an automated test checks that the four buyer-driven explanations remain present. The commit is recorded in repository history alongside this findings update.

## Limitations

This is a small formative usability study, not proof of economic impact. Participants are not representative of all Sri Lankan food buyers; self-reported intent is not observed purchasing behaviour; and the short session does not measure long-term trust or savings. The exact tested commit, devices, setting and facilitator were not recorded in the supplied notes, and the revised wording has not yet been retested with participants.

