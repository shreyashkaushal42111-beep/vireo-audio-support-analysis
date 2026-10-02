# Memo to Priya Raman — Q3 2025 Support Performance Review

**To:** Priya Raman, Head of Customer Experience
**From:** Support Analytics
**Date:** July 2026
**Subject:** Q3 2025 Performance Summary, Training-Review Shortlist, and Data Findings

---

## Executive Summary

This memo summarises verified Q3 2025 support performance figures, identifies a
ten-agent Tier 1 training-review shortlist, and flags data-quality and policy
compliance issues that require separate action. All figures are drawn directly
from the helpdesk export and the operating policy document. Estimates are
clearly distinguished from observed figures. No finding in this memo should be
read as establishing individual employee causation without further review.

---

## Q3 2025 Performance Snapshot (July 1 – September 30, 2025)

Q3 2025 straddles the 14 September system cut-over from Freshdesk to the
current helpdesk. **1,577 tickets** were created in this window; 78% originate
from the legacy system, whose handle-time records are partially unreliable
(see Data Quality section).

| Metric | Q3 2025 (observed) | Full 18-month dataset |
|---|---|---|
| Total tickets | 1,577 | 11,750 |
| Resolved / closed | 1,501 (95.2%) | 11,183 (95.2%) |
| CSAT response rate | 44.0% | 42.1% |
| Average CSAT (1–5 scale) | **3.41** | 3.33 |
| SLA first-response breach rate | **9.6%** | 9.1% |
| Median handle time (valid records) | not computable for Q3* | 33 minutes |

*Q3 handle-time median is unreliable because 55% of Q3 resolved tickets carry
legacy timestamp corruption; the figure is omitted rather than reported
inaccurately.

**Most significant operational finding:** Email has the highest SLA breach rate
(12.2%) across the full dataset despite having the most lenient target (8 hours).
This pattern persists in Q3 and is the clearest signal for process review.

---

## Training-Review Shortlist — Tier 1 Agents Only

All 38 Tier 1 agents were ranked on a composite score: CSAT average (40% weight),
SLA breach rate (40%), and mean handle time (20%). Handle time carries a lower
weight because Logistics and Returns Desk agents handle multi-day fulfilment cases
by design; their longer times partly reflect case type, not solely individual
performance. The full 18-month window was used for per-agent metrics to maximise
sample reliability.

**This is a training-review shortlist, not a disciplinary list.** The methodology
is documented, reproducible, and mathematically consistent across all 11,750
tickets. A sensitivity check (CSAT 50% / SLA 50%, no handle time) confirms that
7 of the same 10 agents appear — the list is not driven by the handle-time
component.

**The 6 agents in Tier 2 (Escalations & Warranty) are excluded from this
ranking.** Their CSAT averages (2.44–2.86) are structurally lower because
escalated warranty cases involve already-dissatisfied customers and multi-day
resolution cycles. Comparing them against Tier 1 on these metrics would be
inappropriate.

| Rank | Agent ID | Name | Team | CSAT (n) | SLA Breach | Mean Handle Time |
|---|---|---|---|---|---|---|
| 1 | A3030 | Geeta Iyer | Logistics | 3.18 (139) | 13.4% | 47.6 hrs |
| 2 | A3028 | Vivaan Pandey | Logistics | 3.12 (145) | 10.6% | 43.3 hrs |
| 3 | A3036 | Divya Tiwari | Returns Desk | 3.28 (103) | 10.5% | 35.9 hrs |
| 4 | A3037 | Mohammed Desai | Returns Desk | 3.29 (234) | 10.1% | 38.7 hrs |
| 5 | A3035 | Nisha Rao | Billing | 3.43 (184) | 11.4% | 7.1 hrs |
| 6= | A3034 | Meera Pereira | Billing | 3.40 (154) | 10.5% | 6.8 hrs |
| 6= | A3029 | Kavya Pandey | Logistics | 3.11 (154) | 7.9% | 43.4 hrs |
| 6= | A3017 | Aadhya Rao | Email Frontline | 3.51 (87) | 11.1% | 9.4 hrs |
| 9 | A3021 | Geeta Sen | Email Frontline | 3.64 (108) | 13.7% | 13.2 hrs |
| 10 | A3006 | Kavya Pandey | Chat Frontline | 3.03 (132) | 8.9% | 5.4 hrs |

CSAT (n) = number of valid survey responses used in the average.
All CSAT blanks are excluded from averages; they are never treated as zero.

---

## Rs 4 Lakh Training Budget — Context

Budget available: Rs 4,00,000.

| Allocation scenario | Per-agent amount |
|---|---|
| Equal split across all 10 agents | Rs 40,000 |
| Concentrated on ranks 1–5 | Rs 80,000 each |
| Concentrated on ranks 1–3 | Rs 1,33,333 each |

For context: Rs 4,00,000 is approximately **49% of one month's estimated blended
contact cost** (Rs 8,17,000/month at ~650 tickets/week × Rs 290/contact, using
policy planning rates). It is equivalent to **2,424 agent-hours** at the fully
loaded rate of Rs 165/hour. No specific training programme cost is quoted here
as none was provided in the supplied data.

---

## Policy Compliance Findings (Require Separate Action)

These are not data errors — they are operational issues found in the ticket data:

1. **6 tickets show both a refund and a replacement issued** — a direct
   violation of policy section 5. Combined anomalous payout: approximately
   Rs 25,577. Policy requires same-day escalation to Team Lead and Finance.
   Ticket IDs: TK-240833, TK-244004, TK-245019, TK-247304, TK-250859, TK-253280.

2. **32 of 37 goodwill refunds exceed the Rs 500 per-ticket cap** (mean
   Rs 3,171; total excess: approximately Rs 99,732). 86% of GW-OTHER credits
   were paid above the authorised limit. Confirm whether offline Team Lead
   approvals exist for these.

---

## Data-Quality Caveats

1. **Legacy handle times are unreliable for 2,309 tickets.** The Freshdesk
   migration reconstructed resolved timestamps incorrectly (UTC/IST mismatch),
   producing negative handle times. These are excluded from all averages.
   Agent A3035 (Nisha Rao, rank 5) has 33% of her handle-time records excluded
   as a result — her handle-time average is based on fewer observations.

2. **35% of tickets have no linked order ID.** This limits any analysis that
   requires joining tickets to purchase-channel or order-value data.

3. **Agent A3017 (Aadhya Rao, rank 6=):** 79 tickets show a mismatch between
   the first-assigned team and the resolving agent with zero transfers recorded.
   This may reflect routing anomalies rather than individual performance.

---

## Recommended Next Steps

1. Run a within-team comparison for the four Logistics/Returns agents (ranks 1–4)
   to confirm whether they also rank at the bottom within their own peer group.
2. Investigate the 32 goodwill cap breaches for compliance.
3. Escalate the 6 dual-payout tickets to Finance per policy section 5.
4. Establish a separate Tier 2 assessment framework for Escalations & Warranty.
5. Investigate agent A3017's routing pattern before attributing performance solely
   to the individual.

---

*All original data files verified unchanged (SHA-256). Analysis is fully
reproducible. See README.md for reproduction commands.*
