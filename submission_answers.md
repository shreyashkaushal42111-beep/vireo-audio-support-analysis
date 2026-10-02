# Submission Answers — Vireo Audio Support Analytics Assessment

---

## Q1. What was built and what business outcome does it support?

A reproducible Python analytics pipeline that ingests five CSV datasets and one
policy PDF to produce:

- **`agent_metrics.csv`** — 44 agents × 20 columns of verified per-agent metrics
- **`bottom_10_agents.csv`** — ranked 10-agent Tier 1 training-review shortlist
- **`memo_to_priya.md`** — non-technical one-page brief for the Head of CX
- **`compute_q3_summary.py`** — Q3 business summary, contact costs, replacement
  costs, and policy compliance findings (printed to stdout)

**Business outcome supported:** Q3 training budget allocation for Priya Raman.
The pipeline identifies which 10 of 38 Tier 1 agents score lowest on a composite
of CSAT (40%), SLA breach rate (40%), and handle time (20%), enabling the
Rs 4,00,000 training budget to be directed at agents most likely to benefit.

**Key numbers:**

| Metric | Value |
|---|---|
| Tickets analysed | 11,750 |
| Agents ranked | 38 Tier 1; 6 Tier 2 reported separately |
| Overall SLA breach rate | 9.1% (1,064 breaches) |
| SLA breach credits outstanding | Rs 3,72,400 (1,064 × Rs 350) |
| Policy replacement cost (1,896 replacements) | Rs 34,15,990 |
| Dual-payout policy violations found | 6 tickets, ~Rs 25,577 anomalous payout |
| Goodwill cap excess | 32 tickets, ~Rs 99,732 excess above Rs 500 cap |
| Estimated monthly contact cost | Rs 8,16,833 (at ~650 tickets/week, blended Rs 290) |
| Training budget as % of monthly contact cost | 49% |

---

## Q2. What does it cost to run per month at approximately 650 tickets/week?

All figures use policy planning rates from `support.pdf` §4. These are
**estimates**, not confirmed company P&L actuals.

| Item | Calculation | Monthly estimate |
|---|---|---|
| Contact volume | 650 tickets/week × 52/12 | ~2,817 tickets/month |
| Blended contact cost | 2,817 × Rs 290 | **Rs 8,16,833** |
| Annualised | Rs 8,16,833 × 12 | **Rs 98,01,996** |
| SLA breach credits | 2,817 × 9.1% × Rs 350 | **Rs 89,270/month** |
| Internal transfers (helpdesk rate) | 871 transfers in 8,376 helpdesk tickets = 10.4%; 2,817 × 10.4% × Rs 305 | **~Rs 89,300/month** (estimate) |

Per-channel cost breakdown for the full dataset (observed, not monthly):

| Channel | Tickets | Rate | Total |
|---|---|---|---|
| Chat | 5,102 | Rs 210 | Rs 10,71,420 |
| Email | 3,644 | Rs 260 | Rs 9,47,440 |
| Voice | 1,833 | Rs 520 | Rs 9,53,160 |
| Social | 1,171 | Rs 240 | Rs 2,81,040 |
| **Total (per-channel)** | **11,750** | | **Rs 32,53,060** |

---

## Q3. What evidence shows it works? Validation checks, reconciliations, error frequency.

`validate_pipeline.py` runs 10 automated checks. **All 10 passed on every run.**

| Check | Result |
|---|---|
| SHA-256 of all 6 original input files match known-good hashes | Pass |
| `agent_metrics.csv` has exactly 44 rows × 20 columns | Pass |
| `bottom_10_agents.csv` has exactly 10 rows × 26 columns | Pass |
| All 44 roster agent IDs present in metrics; none missing or extra | Pass |
| Zero Tier 2 agents in the bottom-10 | Pass |
| Total ticket count reconciles: CSV 11,750 = metrics sum 11,750 | Pass |
| Resolved/closed count reconciles: CSV 11,183 = metrics sum 11,183 | Pass |
| Valid CSAT count reconciles: CSV 4,947 = metrics sum 4,947; no zero imputation | Pass |
| Valid handle-time count reconciles: 8,874 = 8,874; 2,309 exclusions confirmed | Pass |
| SLA breach count reconciles: 1,064 = 1,064 | Pass |

**Key data-quality frequencies discovered during the audit:**

| Issue | Count | % of dataset |
|---|---|---|
| Legacy negative handle times (excluded) | 2,309 | 19.7% |
| `resolved_at` before `created_at` (legacy) | 2,121 | 18.1% |
| Null `order_id` | 4,107 | 35.0% |
| CSAT on open/pending tickets (excluded) | 249 | 2.1% |
| SLA breaches | 1,064 | 9.1% |
| Refund + replacement on same ticket (policy violation) | 6 | 0.05% |
| Zero-transfer team mismatches | 468 | 4.0% |
| Goodwill refunds exceeding Rs 500 cap | 32 of 37 GW-OTHER | 86% |

---

## Q4. What client ask was changed, narrowed, or pushed back on, and why?

1. **Arjun's Rs 2,500 flat replacement cost estimate was not used.** The policy
   document (§5) specifies replacement cost = unit cost + Rs 340 logistics.
   Using the policy formula gives a total of Rs 34,15,990 across 1,896 tickets.
   Using Rs 2,500 flat would give Rs 47,40,000 — an overstatement of
   Rs 13,24,010. The policy figure was used throughout.

2. **Tier 2 agents were excluded from the Tier 1 bottom-10 ranking.** The brief
   asked for a bottom-10 overall, but ranking Tier 2 agents (Escalations &
   Warranty) against Tier 1 on volume or handle-time metrics is explicitly
   inappropriate per the policy and the nature of escalated cases. Tier 2 is
   reported separately with a clear explanation.

3. **Handle time was given reduced weight (20% vs 40% each for CSAT and SLA).**
   A full equal-weight ranking would mechanically place all five Logistics/Returns
   agents in the bottom 10 purely because of case type (their handle times are
   40–50× longer by design). Reducing handle-time weight to 20% and including a
   sensitivity check (CSAT 50%/SLA 50%, no handle time) makes the ranking more
   defensible and less artefactual.

4. **The "bottom-10 training-review shortlist" framing was maintained.** The
   ranking identifies agents who may benefit from targeted training based on three
   metrics. It does not establish individual causation, and the memo explicitly
   avoids language like "worst employees."

---

## Q5. What known bugs, shortcuts, or limitations remain?

1. **All agents have a single static roster row** — no historical team or shift
   changes are captured in the data extract. Agent team/tier is treated as
   constant for the entire 18-month window. If any agent changed teams during
   the period, their metrics are attributed to their current team, not their
   team at time of ticket.

2. **The Q3 date range uses the full 18-month window for agent metrics.** This is
   deliberate (to maximise sample size) but means per-agent CSAT and SLA figures
   are not Q3-only. A quarter-filtered agent view would have smaller, less
   reliable per-agent samples.

3. **231 chat tickets have first_response_at = created_at (FRT = 0 minutes).**
   These are counted as non-breaching. They are likely bot-first responses. If
   the intent is to measure human FRT only, these should be excluded — this
   adjustment was not made because the policy does not explicitly exclude bot
   responses from SLA measurement.

4. **175 tickets have created_at before linked order_date** (67 more than 30 days
   apart). These order linkages are likely wrong but were not removed from the
   dataset. Any order-date-dependent analysis on those tickets would be unreliable.

5. **Legacy `transfers` field:** 311 non-zero values exist in legacy_fd. The
   policy states transfers are tracked only in the current helpdesk. These
   legacy values are included in the data but flagged; they are not excluded
   from the raw flag count.

---

## Q6. What was deliberately left out because of the time/scope limit?

1. **Within-team ranking for Logistics and Returns Desk.** Ranks 1–4 are from
   these two teams. A within-team percentile rank would clarify whether they are
   bottom performers relative to their own peers or are being penalised by case
   mix. Recommended as a next step, not included here.

2. **First-contact resolution (FCR) rate.** Policy §10 defines FCR as no repeat
   contact within 30 days. Computing this requires a 30-day window join on
   `customer_id` per resolved ticket. The data supports it but it was not in
   scope for the core deliverables.

3. **Tier 2 agent assessment.** A separate ranking framework for the 6
   Escalations & Warranty agents requires case-complexity-adjusted benchmarks
   that were not defined in the brief.

4. **Channel-mix shift analysis over time.** Ticket volume grew from ~1,577
   in Q3 2025 to ~3,442 in Q1 2026. Understanding whether the mix (chat/email/
   voice/social) changed meaningfully is useful context but out of scope.

5. **Goodwill cap breach investigation.** 32 tickets exceed the Rs 500 goodwill
   cap. Whether offline Team Lead approvals exist for these is an operational
   check that requires access to non-data sources.

---

## Q7. What extra useful thing was built or discovered?

1. **Policy compliance findings surfaced automatically:** 6 dual-payout
   violations (Rs 25,577) and 32 goodwill cap breaches (Rs 99,732 excess) were
   identified without being part of the original brief. These have immediate
   financial and compliance implications.

2. **The replacement cost correction:** Arjun's Rs 2,500 estimate, if used,
   would have overstated replacement costs by Rs 13,24,010. The policy formula
   was applied correctly.

3. **Sensitivity ranking published alongside main ranking.** The CSAT 50%/SLA
   50% no-handle-time sensitivity check was not requested but was included to
   give the business confidence that the bottom-10 list is robust.

4. **Full data audit documented.** Nine categories of data-quality issues were
   identified, quantified, and documented with business impact before any metric
   was computed. This prevents analytical errors that would otherwise be invisible.

5. **SHA-256 file integrity verification** is embedded in the validation script,
   ensuring original data files can be independently confirmed as unmodified
   at any point.

---

## Q8. How was AI used?

**IBM Bob (IBM's AI coding assistant) was used as the primary coding and
analysis agent throughout this session.** Specifically, Bob was used to:

- Write all four Python scripts from scratch
- Run the scripts iteratively and fix encoding/syntax errors
- Execute all data analysis commands and return results
- Generate the memo, README, and this submission document
- Cross-check figures between the audit phase and the metric outputs
- Maintain the validation pipeline and catch the `b['tier']` bug in the README
  quick-verification snippet before it was published

**What was discarded or required correction:**
- Initial composite ranking had inverted direction logic (good performers were
  landing in "bottom" because the percentile rank direction was wrong). This was
  caught, diagnosed, and corrected before any output was finalised.
- Unicode characters (arrows, em-dashes, section symbols) caused
  `UnicodeEncodeError` on the Windows console. These were found and replaced
  across multiple files in one pass.
- The README quick-verification snippet referenced `b['tier']` which does not
  exist in `bottom_10_agents.csv`. Fixed before publication.

**Screen recording:** The full session in the Bob IDE was recorded and
demonstrates: the data audit, metric calculation, ranking, validation, and
document generation — all within one continuous session with no manual edits
to the output CSVs.

**[PLACEHOLDER — Screen recording Google Drive link: INSERT YOUR LINK HERE]**

> Note: If ChatGPT or any other tool was used for review, guidance, or drafting
> outside of this session, add a sentence here describing that use. Do not
> leave this note in the final submission if no other tool was used.

---

## Q9. Public Google Drive link

**[PLACEHOLDER — Insert your public Google Drive share link here]**

The Drive folder should contain:
- This repository folder (or a zip of it)
- The screen recording
- Any additional context documents

---

## Q10. Three things to hand over on Monday

1. **This repository** — all four Python scripts, the two output CSVs, the memo,
   README, and validation script. A reviewer can run `python validate_pipeline.py`
   to confirm all 10 checks pass on a clean machine with `pandas` and `numpy`
   installed.

2. **The policy compliance finding list** — specifically the 6 dual-payout ticket
   IDs and the 32 goodwill cap breach tickets. These require Finance and Team Lead
   action independent of the training review.

3. **The Tier 2 open question** — the six Escalations & Warranty agents (A3039–
   A3044) were excluded from the Tier 1 ranking. Their CSAT ranges from 2.44 to
   2.86. A separate assessment framework with case-complexity-adjusted benchmarks
   should be scoped before Q4.

---

## Q11. Honest hours spent

**[PLACEHOLDER — Insert your actual hours here]**

Approximate breakdown (for reference):
- Data exploration and audit: ~1.5 hrs
- Metric pipeline development and debugging: ~1.5 hrs
- Ranking, sensitivity analysis, validation: ~1.0 hr
- Memo, README, submission answers: ~0.5 hr
- Total: approximately 4.5–5 hours within the stated scope

---

## Q12. GitHub repository link

**[PLACEHOLDER — Insert your GitHub repository URL here]**

To reproduce all outputs from the repository on a clean machine:

```bash
pip install pandas numpy
python compute_agent_metrics.py
python rank_bottom_10.py
python validate_pipeline.py
python compute_q3_summary.py
```

Expected result of `validate_pipeline.py`: **10 checks passed, 0 errors.**
