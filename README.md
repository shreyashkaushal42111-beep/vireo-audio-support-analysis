# Vireo Audio — Support Analytics Assessment

## Overview

This repository contains a reproducible data analysis pipeline for the Vireo
Audio Pvt. Ltd. customer support Q3 performance review. It ingests five CSV
datasets and one policy PDF, produces agent-level metrics, identifies a
ten-agent training-review shortlist, and generates supporting business
summaries.

---

## Requirements

### Python Version

Python **3.10 or later** is required. Tested on Python 3.13.

### Packages

```
pandas>=2.0
numpy>=1.24
```

Install with:

```bash
pip install pandas numpy
```

No other packages are needed. The pipeline does not use matplotlib, scipy,
or any external API.

---

## Folder Structure

```
Vireo_Audio_Assessment/
│
├── README.md                        <- This file
├── memo_to_priya.md                 <- Non-technical summary memo (to Priya Raman)
├── submission_answers.md            <- Assessment submission Q&A
│
├── compute_agent_metrics.py         <- Step 1: per-agent metric calculation
├── compute_q3_summary.py            <- Step 2: business summary, costs, replacements
├── rank_bottom_10.py                <- Step 3: composite ranking, bottom-10 export
├── validate_pipeline.py             <- Step 4: full end-to-end validation
│
├── agent_metrics.csv                <- OUTPUT: all 44 agents, all metrics
├── bottom_10_agents.csv             <- OUTPUT: bottom-10 Tier 1 agents ranked
│
├── AGENTS.md                        <- Agent/AI context file (documentation only)
├── .bob/                            <- Bob IDE mode-specific context files
│
│   [INPUT DATA — do not modify]
├── ef56a2c7-...-tickets.csv         <- 11,750 support tickets
├── 8fb10115-...-agents.csv          <- 44 agent roster rows
├── 8fb10115-...(1).csv              <- Identical duplicate of agents.csv (ignore)
├── 1e2a735c-...-customers.csv       <- 9,500 customer records
├── 6990ae61-...-orders.csv          <- 15,500 orders
├── c59ac66f-...-products.csv        <- 14 products
└── support.pdf                      <- Operating policy (authoritative rules)
```

---

## Running the Pipeline

Run the three scripts **in order** from the project directory.
Each script is self-contained and reads only from the original CSV files.
No script modifies any original file.

### Step 1 — Compute agent metrics

```bash
python compute_agent_metrics.py
```

**Reads:** tickets.csv, agents.csv, orders.csv
**Writes:** `agent_metrics.csv` (44 rows × 20 columns)
**Time:** ~5 seconds

### Step 2 — Compute Q3 business summary

```bash
python compute_q3_summary.py
```

**Reads:** tickets.csv, agents.csv, orders.csv, products.csv
**Writes:** nothing (prints to stdout only)
**Time:** ~5 seconds

Redirect to a file if you want to save the output:

```bash
python compute_q3_summary.py > q3_summary.txt
```

### Step 3 — Rank and export bottom 10

```bash
python rank_bottom_10.py
```

**Reads:** `agent_metrics.csv` (produced by Step 1)
**Writes:** `bottom_10_agents.csv` (10 rows × 26 columns)
**Time:** <1 second

### Step 4 — Validate all outputs

```bash
python validate_pipeline.py
```

**Reads:** all input CSVs + `agent_metrics.csv` + `bottom_10_agents.csv`
**Writes:** nothing (prints pass/fail to stdout; exits with code 1 on any failure)
**Time:** ~5 seconds
**Expected result:** `PASSED: all checks passed` — 10 checks, 0 errors

---

## Expected Output Files

| File | Rows | Columns | Description |
|---|---|---|---|
| `agent_metrics.csv` | 44 | 20 | Per-agent metrics, all tiers |
| `bottom_10_agents.csv` | 10 | 26 | Bottom-10 Tier 1 agents with component scores and flags |

### agent_metrics.csv columns

| Column | Description |
|---|---|
| agent_id … tier | Identity from agents.csv |
| total_tickets | All tickets resolved to this agent |
| resolved_closed_volume | Status ∈ {resolved, closed} — the "attendance" definition |
| csat_mean | Mean of valid CSAT scores (blank = excluded, never zero) |
| csat_response_count | Count of non-null CSAT on resolved/closed tickets |
| handle_time_mean_mins | Mean (first_response_at → resolved_at), non-negative only |
| handle_time_valid_count | Tickets used in handle-time mean |
| sla_breach_rate | Breached ÷ total; channel targets: chat 15 min, voice 120 min, social 240 min, email 480 min |
| sla_breach_count / sla_eligible_count | Raw breach numerator and denominator |
| flag_legacy_handle_excluded | Count of legacy_fd tickets with negative handle time excluded |
| flag_dual_payout_tickets | Count of refund+replacement policy violations |
| flag_csat_on_open_pending | CSAT present on unresolved tickets (excluded from mean) |
| flag_zero_xfer_team_mismatch | Assigned-team ≠ resolving-agent team with transfers=0 |
| flag_ticket_before_order | Ticket created before linked order date |

### bottom_10_agents.csv additional columns

| Column | Description |
|---|---|
| badscore_csat / badscore_sla / badscore_ht | Per-metric percentile bad-score (0–1; 1.0 = worst) |
| composite_bad_score | Weighted sum: CSAT 40% + SLA 40% + handle time 20% |
| overall_rank | Rank within Tier 1 pool (1 = worst composite score) |
| sensitivity_rank | Rank if handle time is excluded (CSAT 50%, SLA 50%) |
| small_csat_sample | True if csat_response_count < 50 |
| high_legacy_exclusion | True if >30% of handle-time records excluded due to legacy timestamps |

---

## Verifying the Outputs

### Quick verification

```bash
python -c "
import pandas as pd
m = pd.read_csv('agent_metrics.csv')
b = pd.read_csv('bottom_10_agents.csv')
assert len(m) == 44, f'Expected 44 agents, got {len(m)}'
assert len(b) == 10, f'Expected 10 rows, got {len(b)}'
assert m['total_tickets'].sum() == 11750, 'Ticket count mismatch'
b_tier = b.merge(m[['agent_id','tier']], on='agent_id')
assert (b_tier['tier'] == 1).all(), 'Tier 2 agent found in bottom-10'
assert b['agent_id'].nunique() == 10, 'Duplicate agent IDs in bottom-10'
assert set(b['agent_id']).issubset(set(m['agent_id'])), 'Unknown agent IDs in bottom-10'
print('All assertions passed.')
print(f'  agent_metrics.csv:    {len(m)} rows, {len(m.columns)} columns')
print(f'  bottom_10_agents.csv: {len(b)} rows, {len(b.columns)} columns')
"
```

Or run the full validation script (recommended):

```bash
python validate_pipeline.py
```

### Verify original files are unchanged (SHA-256)

```bash
python -c "
import hashlib, pathlib
expected = {
    'ef56a2c7-7840-454e-ab7e-a0df87b90bc5-tickets.csv':   'CD5FD9BB8883F26B1CF7932DCA9C0770C67D01EA22ECD456571DDF8CA5400D1B',
    '8fb10115-c45d-42dc-9e04-95154d9c3e41-agents.csv':    '7A396590C585FDF0D36120C9240208E834C5BC6B1039CD7AD0FB01E1C05DF1A2',
    '6990ae61-2433-405d-a790-24fda9cb7743-orders.csv':    'BF399F4FBCD067EC4515618543BD500EDE6CB36BED1AADEF9219B9565BE7A240',
    '1e2a735c-5a79-4c67-9fc0-e0006ea2b76a-customers.csv': '91EE520527A7E80BDD7EA286E621EAAB219B79028D4252FA66A2AC52F759F9BF',
    'c59ac66f-a215-4a8a-8dfe-39fc4db60f5c-products.csv':  'E81B4A60E0D3B37FCB9580FE5B0221667541C3FE38BEFF11E0EE37A3FD0A48D8',
    'support.pdf':                                         'C1778EC66E5895786A451615C91E61FB53FD81B58BD8DE09CD5D3B63B24A10CF',
}
for fname, exp_hash in expected.items():
    data = pathlib.Path(fname).read_bytes()
    actual = hashlib.sha256(data).hexdigest().upper()
    status = 'OK' if actual == exp_hash else 'CHANGED!'
    print(f'{status}  {fname}')
"
```

---

## Reproducing the Full Pipeline

```bash
python compute_agent_metrics.py
python rank_bottom_10.py
python validate_pipeline.py
python compute_q3_summary.py
```

Steps 1 and 3 produce the output CSVs. Step 4 validates them.
Step 2 (`compute_q3_summary.py`) prints the business summary to stdout;
redirect to a file if needed: `python compute_q3_summary.py > q3_summary.txt`

---

## Known Data-Quality Limitations

These are documented in the data audit. Analysts working with the outputs should
be aware of the following:

| Issue | Count | Impact |
|---|---|---|
| Legacy negative handle times | 2,309 | Excluded from handle-time means; affects 38 Tier 1 agents |
| `resolved_at` < `created_at` (legacy) | 2,121 | Same root cause; UTC/IST reconstruction error in Freshdesk migration |
| Null `order_id` | 4,107 (35%) | Limits order-level analysis |
| CSAT on open/pending tickets | 249 | Excluded from CSAT averages |
| Refund + replacement on same ticket | 6 | Policy violation; ~Rs 25,577 anomalous payout |
| Zero-transfer team mismatches | 468 | Possible under-counted transfers |
| Ticket before order date | 175 | Likely wrong `order_id` linkage; 67 > 30 days apart |
| Goodwill refunds > Rs 500 cap | 32 of 37 | 86% of GW-OTHER tickets exceed authorised limit |

### Legacy timestamp issue (critical)

The previous helpdesk (Freshdesk, `source_system = legacy_fd`) exported
timestamps in UTC. When tickets were migrated, `created_at` was stored in IST
but `resolved_at` was reconstructed from UTC event logs. This creates a
systematic ~4–6 hour discrepancy that makes `resolved_at < created_at` for
2,121 tickets and produces negative handle times for 2,309 tickets.

**Rule:** Never use handle time from legacy_fd tickets unless the specific
ticket's `resolved_at` > `first_response_at` (i.e. handle_mins >= 0).

### CSAT blanks

A blank `csat_score` means the customer did not respond to the survey.
It is **never** treated as a score of zero. The overall non-response rate is
~56%, consistent with the policy's stated ~45% response rate.

### All-active roster

All 44 agents have a single roster row with `to_date` blank (currently active).
No historical team or shift changes are recorded. Agent team/tier is therefore
treated as constant for the full analysis window.

---

## Q3 Date Range Decision

The analysis labels itself "Q3" in line with the assessment brief.
The data spans January 2025 to June 2026. The business summary uses
**Calendar Q3 2025 = July 1 – September 30, 2025** as the Q3 window.
The agent-level metrics (agent_metrics.csv, bottom_10_agents.csv) use the
**full 18-month window** to maximise per-agent sample sizes and statistical
reliability, which is the standard approach for agent performance reviews.

---

## Contact

Analysis produced as part of the Vireo Audio support assessment.
Scripts are self-contained and can be re-run against updated data exports
by replacing the input CSV files and rerunning Steps 1–3.
