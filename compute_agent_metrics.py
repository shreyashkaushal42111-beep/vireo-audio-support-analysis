"""
compute_agent_metrics.py
========================
Calculates agent-level core metrics for the Vireo Audio support assessment.

METHODOLOGY NOTES
-----------------

A. Agent-level CSAT
   - Source: tickets.csat_score
   - Blank csat_score means NO survey response. These are EXCLUDED from the
     average; they are NOT treated as zero.
   - Scope: Only resolved or closed tickets where csat_score is not null.
   - Result: mean of integer scores 1-5.

B. Agent-level handle time
   - Definition per policy §10: first_response_at → resolved_at.
   - Only tickets with status resolved or closed (i.e. resolved_at is not null).
   - EXCLUSION 1: All legacy_fd tickets with resolved_at < created_at are
     flagged as timestamp-corrupted. Their handle times (which are negative
     due to the UTC/IST reconstruction error documented in the audit) are
     EXCLUDED from the mean. The excluded count is reported in the flags column.
   - EXCLUSION 2: Tickets where first_response_at == resolved_at (zero handle
     time) are retained; zero is a legitimate value for bot-resolved chats.
   - Result: mean handle time in minutes, computed only over valid tickets.

C. Number of valid CSAT responses per agent
   - Count of resolved/closed tickets where csat_score is not null.

D. Number of valid handle-time tickets per agent
   - Count of resolved/closed tickets with a non-negative handle time.

E. SLA breach rate per agent
   - Breach definition: first_response_at - created_at > channel SLA target.
   - Targets: chat 15 min, voice 120 min, social 240 min, email 480 min.
   - Scope: ALL tickets assigned to the agent (resolved, closed, open, pending)
     because the breach happens at first response, which exists for all tickets.
   - Result: breached_count / total_tickets_with_frt (as a fraction 0-1).
   - NOTE: 231 chat tickets with FRT=0 are counted as non-breaching. These are
     likely bot-first responses. No adjustment is made without further evidence.

F. Resolved/closed ticket volume per agent
   - Count of tickets with status in (resolved, closed).
   - This is the "attendance" definition from policy §10.

G. Team and tier
   - Sourced from agents.csv joined on agent_id.
   - Single roster row per agent (no historical changes in this extract).

H. Data-quality flags per agent (counts, not booleans)
   - legacy_handle_excluded : legacy_fd tickets with negative handle time
     (resolved_at < first_response_at), excluded from handle-time mean.
   - both_refund_and_replacement : tickets violating the no-dual-payout rule.
   - csat_on_open_pending : CSAT scores present on unresolved tickets
     (excluded from CSAT mean but counted here).
   - zero_transfer_team_mismatch : resolved/assigned team mismatch with
     transfers=0, indicating possible under-counted transfers.
   - ticket_before_order : ticket created_at precedes linked order_date.

OUTPUT
------
agent_metrics.csv — one row per agent_id.
"""

import pandas as pd
import numpy as np

# ── File paths ────────────────────────────────────────────────────────────────
TICKETS_FILE  = "ef56a2c7-7840-454e-ab7e-a0df87b90bc5-tickets.csv"
AGENTS_FILE   = "8fb10115-c45d-42dc-9e04-95154d9c3e41-agents.csv"
ORDERS_FILE   = "6990ae61-2433-405d-a790-24fda9cb7743-orders.csv"
OUTPUT_FILE   = "agent_metrics.csv"

# ── SLA targets (minutes) ─────────────────────────────────────────────────────
SLA_TARGETS = {
    "chat":   15,
    "email":  480,
    "voice":  120,
    "social": 240,
}

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")
tickets = pd.read_csv(TICKETS_FILE, low_memory=False)
agents  = pd.read_csv(AGENTS_FILE)
orders  = pd.read_csv(ORDERS_FILE)

# ── Parse timestamps ──────────────────────────────────────────────────────────
for col in ["created_at", "first_response_at", "resolved_at"]:
    tickets[col] = pd.to_datetime(tickets[col])
orders["order_date"] = pd.to_datetime(orders["order_date"])

print(f"  tickets: {len(tickets):,} rows")
print(f"  agents:  {len(agents):,} rows")
print(f"  orders:  {len(orders):,} rows")

# ── Derived fields on tickets ─────────────────────────────────────────────────

# First-response time (minutes): always calculated from raw timestamps.
# first_response_at is never null in this dataset (confirmed in audit).
tickets["frt_mins"] = (
    tickets["first_response_at"] - tickets["created_at"]
).dt.total_seconds() / 60

# Handle time (minutes): first_response_at → resolved_at.
tickets["handle_mins"] = (
    tickets["resolved_at"] - tickets["first_response_at"]
).dt.total_seconds() / 60

# SLA breach flag (True = breached).
tickets["sla_target_mins"] = tickets["channel"].map(SLA_TARGETS)
tickets["is_breach"] = tickets["frt_mins"] > tickets["sla_target_mins"]

# Resolved/closed flag.
tickets["is_resolved_closed"] = tickets["status"].isin(["resolved", "closed"])

# ── Data-quality flags on individual tickets ──────────────────────────────────

# Flag 1: Legacy tickets with negative handle time (timestamp corruption).
# These must be excluded from handle-time averages.
tickets["flag_legacy_neg_handle"] = (
    (tickets["source_system"] == "legacy_fd") &
    (tickets["handle_mins"] < 0)
)

# Flag 2: Tickets with BOTH a refund AND replacement_issued=Y (policy violation).
tickets["flag_dual_payout"] = (
    tickets["refund_amount_inr"].notna() &
    (tickets["replacement_issued"] == "Y")
)

# Flag 3: CSAT present on open/pending tickets.
# These are excluded from CSAT means (ticket not yet resolved).
tickets["flag_csat_on_open"] = (
    tickets["csat_score"].notna() &
    ~tickets["is_resolved_closed"]
)

# Flag 4: Resolved/assigned team mismatch with transfers=0.
# Potential under-counted transfers or mis-routing.
agent_team_map = agents.set_index("agent_id")["team"]
tickets["resolving_agent_team"] = tickets["agent_id"].map(agent_team_map)
tickets["flag_zero_xfer_mismatch"] = (
    (tickets["assigned_team"] != tickets["resolving_agent_team"]) &
    (tickets["transfers"] == 0)
)

# Flag 5: Ticket created before linked order date.
tickets_with_order = tickets[tickets["order_id"].notna()].merge(
    orders[["order_id", "order_date"]], on="order_id", how="left"
)
bad_order_link = set(
    tickets_with_order.loc[
        tickets_with_order["created_at"].dt.normalize() < tickets_with_order["order_date"],
        "ticket_id"
    ]
)
tickets["flag_ticket_before_order"] = tickets["ticket_id"].isin(bad_order_link)

# ── Define valid subsets ──────────────────────────────────────────────────────

# Valid for CSAT: resolved or closed AND csat_score not null AND not on open ticket
csat_valid = tickets[
    tickets["is_resolved_closed"] &
    tickets["csat_score"].notna()
]

# Valid for handle time: resolved or closed AND handle_mins >= 0
#   (excludes legacy corrupted negatives)
handle_valid = tickets[
    tickets["is_resolved_closed"] &
    (tickets["handle_mins"] >= 0)
]

# ── Aggregate per agent ────────────────────────────────────────────────────────
print("Aggregating metrics per agent...")

# F: Resolved/closed volume
volume = (
    tickets[tickets["is_resolved_closed"]]
    .groupby("agent_id")
    .size()
    .rename("resolved_closed_volume")
)

# Total tickets (all statuses, for SLA denominator)
total_tickets = (
    tickets
    .groupby("agent_id")
    .size()
    .rename("total_tickets")
)

# A + C: CSAT mean and count
csat_agg = (
    csat_valid
    .groupby("agent_id")["csat_score"]
    .agg(
        csat_mean="mean",
        csat_response_count="count"
    )
)

# B + D: Handle time mean and count (valid tickets only)
handle_agg = (
    handle_valid
    .groupby("agent_id")["handle_mins"]
    .agg(
        handle_time_mean_mins="mean",
        handle_time_valid_count="count"
    )
)

# E: SLA breach rate
sla_agg = tickets.groupby("agent_id").apply(
    lambda g: pd.Series({
        "sla_breach_count":  int(g["is_breach"].sum()),
        "sla_eligible_count": int(g["frt_mins"].notna().sum()),
        "sla_breach_rate":   round(g["is_breach"].mean(), 6),
    }),
    include_groups=False
)

# H: Data-quality flag counts
flags_agg = tickets.groupby("agent_id").agg(
    flag_legacy_handle_excluded    =("flag_legacy_neg_handle",   "sum"),
    flag_dual_payout_tickets       =("flag_dual_payout",         "sum"),
    flag_csat_on_open_pending      =("flag_csat_on_open",        "sum"),
    flag_zero_xfer_team_mismatch   =("flag_zero_xfer_mismatch",  "sum"),
    flag_ticket_before_order       =("flag_ticket_before_order", "sum"),
).astype(int)

# G: Agent metadata
agent_meta = agents[["agent_id", "name", "site", "team", "shift", "tier"]].copy()

# ── Combine all metrics ────────────────────────────────────────────────────────
metrics = (
    agent_meta
    .merge(total_tickets,  on="agent_id", how="left")
    .merge(volume,         on="agent_id", how="left")
    .merge(csat_agg,       on="agent_id", how="left")
    .merge(handle_agg,     on="agent_id", how="left")
    .merge(sla_agg,        on="agent_id", how="left")
    .merge(flags_agg,      on="agent_id", how="left")
)

# Fill agents with zero tickets in a category
metrics["resolved_closed_volume"]    = metrics["resolved_closed_volume"].fillna(0).astype(int)
metrics["csat_response_count"]       = metrics["csat_response_count"].fillna(0).astype(int)
metrics["handle_time_valid_count"]   = metrics["handle_time_valid_count"].fillna(0).astype(int)
metrics["sla_breach_count"]          = metrics["sla_breach_count"].fillna(0).astype(int)
metrics["sla_eligible_count"]        = metrics["sla_eligible_count"].fillna(0).astype(int)
metrics["total_tickets"]             = metrics["total_tickets"].fillna(0).astype(int)

# Round continuous metrics
metrics["csat_mean"]                 = metrics["csat_mean"].round(4)
metrics["handle_time_mean_mins"]     = metrics["handle_time_mean_mins"].round(2)
metrics["sla_breach_rate"]           = metrics["sla_breach_rate"].round(6)

# ── Ordered columns ────────────────────────────────────────────────────────────
col_order = [
    # Identity
    "agent_id", "name", "site", "team", "shift", "tier",
    # Volume (F)
    "total_tickets", "resolved_closed_volume",
    # CSAT (A, C)
    "csat_mean", "csat_response_count",
    # Handle time (B, D)
    "handle_time_mean_mins", "handle_time_valid_count",
    # SLA (E)
    "sla_breach_rate", "sla_breach_count", "sla_eligible_count",
    # Data quality flags (H)
    "flag_legacy_handle_excluded",
    "flag_dual_payout_tickets",
    "flag_csat_on_open_pending",
    "flag_zero_xfer_team_mismatch",
    "flag_ticket_before_order",
]
metrics = metrics[col_order].sort_values("agent_id").reset_index(drop=True)

# ── Write output ───────────────────────────────────────────────────────────────
metrics.to_csv(OUTPUT_FILE, index=False)
print(f"\nWrote {len(metrics)} rows to {OUTPUT_FILE}")

# ── Console summary ────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("AGENT METRICS SUMMARY")
print("="*70)

t1 = metrics[metrics["tier"] == 1]
t2 = metrics[metrics["tier"] == 2]
print(f"\nTier 1 agents: {len(t1)}   |   Tier 2 agents: {len(t2)}")

print(f"\n--- TIER 1 AGENTS ({len(t1)}) ---")
print(t1[[
    "agent_id","name","team","resolved_closed_volume",
    "csat_mean","csat_response_count",
    "handle_time_mean_mins","handle_time_valid_count",
    "sla_breach_rate","sla_breach_count",
    "flag_legacy_handle_excluded"
]].to_string(index=False))

print(f"\n--- TIER 2 AGENTS ({len(t2)}) ---")
print(t2[[
    "agent_id","name","team","resolved_closed_volume",
    "csat_mean","csat_response_count",
    "handle_time_mean_mins","handle_time_valid_count",
    "sla_breach_rate","sla_breach_count",
    "flag_legacy_handle_excluded"
]].to_string(index=False))

print(f"\n--- DATA QUALITY FLAG SUMMARY ---")
flag_cols = [
    "flag_legacy_handle_excluded",
    "flag_dual_payout_tickets",
    "flag_csat_on_open_pending",
    "flag_zero_xfer_team_mismatch",
    "flag_ticket_before_order",
]
flag_summary = metrics[flag_cols].sum()
print(flag_summary.to_string())
agents_with_flags = (metrics[flag_cols] > 0).any(axis=1).sum()
print(f"\nAgents with at least one flag: {agents_with_flags} / {len(metrics)}")

print(f"\n--- CROSS-CHECKS ---")
print(f"Total tickets in dataset:            {len(tickets):,}")
print(f"Sum of all total_tickets in output:  {metrics['total_tickets'].sum():,}")
print(f"All 44 agents present in output:     {len(metrics) == 44}")

print(f"\n--- METRIC COVERAGE (Tier 1 only) ---")
print(f"Agents with >= 1 valid CSAT:         {(t1['csat_response_count'] >= 1).sum()} / {len(t1)}")
print(f"Agents with >= 1 valid handle time:  {(t1['handle_time_valid_count'] >= 1).sum()} / {len(t1)}")
print(f"Agents with >= 10 valid CSAT:        {(t1['csat_response_count'] >= 10).sum()} / {len(t1)}")
