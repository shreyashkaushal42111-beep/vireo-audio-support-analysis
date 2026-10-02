"""
rank_bottom_10.py
=================
Produces a composite performance ranking of all Tier 1 agents and exports:
  - agent_metrics.csv   (already produced by compute_agent_metrics.py; confirmed valid)
  - bottom_10_agents.csv

RANKING METHODOLOGY
-------------------

Population: Tier 1 agents only (38 agents).
Tier 2 (Escalations & Warranty, 6 agents) are reported separately and are
NOT included in the bottom-10 ranking.  Policy §6 and the data audit confirm
that Tier 2 handle multi-touch warranty cases measured in days, not tickets
per week; comparing them with Tier 1 on volume or handle-time would be
inappropriate.

Metrics used and their weights
-------------------------------
Three primary metrics are used.  Handle time carries reduced weight because
it is structurally team-dependent: Logistics/Returns agents handle fulfilment
and returns cases that inherently take 40-50x longer than a chat query.
Including it at equal weight would mechanically push every Logistics/Returns
agent into the bottom 10 regardless of their actual relative performance.

  Metric                    Weight   Direction (worse = ?)
  ─────────────────────────────────────────────────────────
  csat_mean                  40 %    LOW  is worse
  sla_breach_rate            40 %    HIGH is worse
  handle_time_mean_mins      20 %    HIGH is worse (within-team context, see flags)

Scoring method: percentile rank within the 38-agent Tier 1 pool.
  • For LOW-is-worse metrics (CSAT): bad_score = 1 − pct_rank(ascending=True)
    → agent with lowest CSAT gets bad_score ≈ 1.0
  • For HIGH-is-worse metrics (SLA breach, handle time):
      bad_score = pct_rank(ascending=True)
    → agent with highest breach rate / longest handle time gets bad_score ≈ 1.0

Composite bad score = 0.40 × bad_csat + 0.40 × bad_sla + 0.20 × bad_ht
Range 0–1; higher = worse overall performance.

Reliability flags carried into the output
------------------------------------------
  small_csat_sample    : csat_response_count < 50  (average less reliable)
  high_legacy_exclusion: flag_legacy_handle_excluded / resolved_closed_volume > 0.30
                         (handle time computed on <70% of resolved tickets)
  Any flagged metric is noted explicitly in the bottom_10_agents.csv so the
  training-review team can weight those cells accordingly.

A sensitivity check (CSAT 50% + SLA 50%, no handle time) is printed to
confirm the bottom 10 is not driven by the handle-time component.
"""

import pandas as pd
import numpy as np

INPUT_METRICS  = "agent_metrics.csv"
OUTPUT_BOTTOM  = "bottom_10_agents.csv"

# ── Load agent metrics ────────────────────────────────────────────────────────
m = pd.read_csv(INPUT_METRICS)
print(f"Loaded {len(m)} agents from {INPUT_METRICS}")

# ── Tier split ────────────────────────────────────────────────────────────────
t1 = m[m["tier"] == 1].copy().reset_index(drop=True)
t2 = m[m["tier"] == 2].copy().reset_index(drop=True)
print(f"  Tier 1: {len(t1)} agents  |  Tier 2: {len(t2)} agents")

# ── Reliability flags ─────────────────────────────────────────────────────────
t1["small_csat_sample"]     = t1["csat_response_count"] < 50
t1["high_legacy_exclusion"] = (
    t1["flag_legacy_handle_excluded"] / t1["resolved_closed_volume"] > 0.30
)

# ── Percentile bad-scores (0–1; 1.0 = worst on that metric) ──────────────────
# CSAT: low is bad → bad_score = 1 − pct_rank_ascending
t1["badscore_csat"] = 1 - t1["csat_mean"].rank(pct=True, ascending=True)

# SLA breach: high is bad → bad_score = pct_rank_ascending
t1["badscore_sla"]  = t1["sla_breach_rate"].rank(pct=True, ascending=True)

# Handle time: high is bad → bad_score = pct_rank_ascending
t1["badscore_ht"]   = t1["handle_time_mean_mins"].rank(pct=True, ascending=True)

# ── Composite score ───────────────────────────────────────────────────────────
W_CSAT = 0.40
W_SLA  = 0.40
W_HT   = 0.20

t1["composite_bad_score"] = (
    W_CSAT * t1["badscore_csat"] +
    W_SLA  * t1["badscore_sla"]  +
    W_HT   * t1["badscore_ht"]
).round(6)

# Rank within Tier 1: rank 1 = worst composite score (most in need of review)
t1["overall_rank"] = t1["composite_bad_score"].rank(
    method="min", ascending=False
).astype(int)

t1_ranked = t1.sort_values("overall_rank").reset_index(drop=True)

# ── Sensitivity check (CSAT 50%, SLA 50%, no handle time) ───────────────────
t1_ranked["sensitivity_no_ht"] = (
    0.50 * t1_ranked["badscore_csat"] +
    0.50 * t1_ranked["badscore_sla"]
).round(6)
t1_ranked["sensitivity_rank"] = t1_ranked["sensitivity_no_ht"].rank(
    method="min", ascending=False
).astype(int)

# ── Bottom 10 selection ───────────────────────────────────────────────────────
bottom_10 = t1_ranked[t1_ranked["overall_rank"] <= 10].copy()

# ── Build bottom_10_agents.csv ────────────────────────────────────────────────
b10_cols = [
    "overall_rank",
    "agent_id", "name", "site", "team", "shift",
    # Volume
    "resolved_closed_volume",
    # CSAT
    "csat_mean", "csat_response_count", "small_csat_sample",
    # Handle time
    "handle_time_mean_mins", "handle_time_valid_count", "high_legacy_exclusion",
    # SLA
    "sla_breach_rate", "sla_breach_count", "sla_eligible_count",
    # Component bad-scores
    "badscore_csat", "badscore_sla", "badscore_ht",
    # Composite
    "composite_bad_score",
    # Sensitivity rank (no handle time)
    "sensitivity_rank",
    # Raw data-quality flags
    "flag_legacy_handle_excluded",
    "flag_dual_payout_tickets",
    "flag_csat_on_open_pending",
    "flag_zero_xfer_team_mismatch",
    "flag_ticket_before_order",
]
bottom_10[b10_cols].to_csv(OUTPUT_BOTTOM, index=False)
print(f"\nWrote {len(bottom_10)} rows to {OUTPUT_BOTTOM}")

# ── Console report ─────────────────────────────────────────────────────────────
SEP = "=" * 90

print(f"\n{SEP}")
print("BOTTOM 10 TIER 1 AGENTS -- Q3 TRAINING REVIEW CANDIDATES")
print(f"Composite score: CSAT {int(W_CSAT*100)}%  |  SLA breach {int(W_SLA*100)}%  |  Handle time {int(W_HT*100)}%")
print(SEP)

display_cols = [
    "overall_rank", "agent_id", "name", "team",
    "csat_mean", "csat_response_count",
    "sla_breach_rate", "sla_breach_count",
    "handle_time_mean_mins", "handle_time_valid_count",
    "composite_bad_score", "sensitivity_rank",
    "small_csat_sample", "high_legacy_exclusion",
]
print(bottom_10[display_cols].to_string(index=False))

print(f"\n{SEP}")
print("RELIABILITY FLAGS IN THE BOTTOM 10")
print(SEP)
for _, row in bottom_10.iterrows():
    flags = []
    if row["small_csat_sample"]:
        flags.append(f"[!] SMALL CSAT SAMPLE ({int(row['csat_response_count'])} responses -- treat mean with caution)")
    if row["high_legacy_exclusion"]:
        pct = int(row["flag_legacy_handle_excluded"] / row["resolved_closed_volume"] * 100)
        flags.append(f"[!] HIGH LEGACY EXCLUSION ({pct}% of handle-time records excluded due to timestamp corruption)")
    if row["flag_dual_payout_tickets"] > 0:
        flags.append(f"[!] {int(row['flag_dual_payout_tickets'])} dual-payout policy violation(s) on this agent's tickets")
    if row["flag_zero_xfer_team_mismatch"] > 0:
        flags.append(f"[!] {int(row['flag_zero_xfer_team_mismatch'])} zero-transfer team mismatches (possible routing anomaly)")
    flag_str = "; ".join(flags) if flags else "None"
    print(f"  #{int(row['overall_rank'])} {row['agent_id']} {row['name']:20s}  Flags: {flag_str}")

print(f"\n{SEP}")
print("SENSITIVITY CHECK -- Bottom 10 if handle time is excluded (CSAT 50%, SLA 50%)")
print(SEP)
sens_bottom = t1_ranked[t1_ranked["sensitivity_rank"] <= 10].sort_values("sensitivity_rank")
print(sens_bottom[[
    "sensitivity_rank", "agent_id", "name", "team",
    "csat_mean", "sla_breach_rate", "sensitivity_no_ht",
]].to_string(index=False))

print(f"\n{SEP}")
print("FULL TIER 1 RANKING (all 38 agents)")
print(SEP)
all_t1_cols = [
    "overall_rank", "agent_id", "name", "team",
    "csat_mean", "csat_response_count",
    "sla_breach_rate", "sla_breach_count",
    "handle_time_mean_mins", "handle_time_valid_count",
    "composite_bad_score",
    "small_csat_sample", "high_legacy_exclusion",
]
print(t1_ranked[all_t1_cols].to_string(index=False))

print(f"\n{SEP}")
print("TIER 2 -- ESCALATIONS & WARRANTY (reported separately; NOT ranked against Tier 1)")
print("Tier 2 agents handle multi-touch warranty cases measured in days.")
print("Volume and handle-time metrics are NOT comparable with Tier 1.")
print(SEP)
t2_display = [
    "agent_id", "name",
    "resolved_closed_volume",
    "csat_mean", "csat_response_count",
    "handle_time_mean_mins",
    "sla_breach_rate", "sla_breach_count",
]
print(t2[t2_display].to_string(index=False))

print(f"\n{SEP}")
print("NOTES AND LIMITATIONS")
print(SEP)
notes = [
    "1. CSAT blanks are excluded from all averages (never treated as zero).",
    "2. Handle time = first_response_at to resolved_at (policy section 10).",
    "3. Negative legacy handle times (2,309 records, all source_system=legacy_fd) are",
    "   excluded. These result from a UTC/IST reconstruction error in the Freshdesk",
    "   migration -- not from actual fast resolution.",
    "4. Handle time weights are reduced (20%) because Logistics and Returns Desk",
    "   handle multi-day fulfilment/returns cases by design. Their long handle times",
    "   reflect case type, not necessarily poor performance. Within-team context",
    "   should supplement this ranking for those teams.",
    "5. Agents A3023 (Meera Patel, 42 CSAT) and A3026 (Suresh Pereira, 40 CSAT)",
    "   have the smallest valid CSAT sample sizes and are flagged accordingly.",
    "   Their CSAT averages are less statistically reliable.",
    "6. assigned_team = first-routed team; agent_id = resolving agent.",
    "   All metrics are attributed to the resolving agent, consistent with",
    "   how SLA breach is reported in policy section 3.",
    "7. Tier 2 agents are NOT in this ranking. Their CSAT (2.44 to 2.86) is",
    "   lower than Tier 1 (2.96 to 3.82) by nature of escalated case complexity.",
    "8. Six tickets across the dataset show both a refund and replacement_issued=Y,",
    "   violating policy section 5. These are distributed across multiple agents.",
    "9. The sensitivity ranking (CSAT 50%, SLA 50%, no handle time) is provided",
    "   to confirm the bottom-10 list is not artefactually driven by handle time.",
]
for note in notes:
    print(f"  {note}")
