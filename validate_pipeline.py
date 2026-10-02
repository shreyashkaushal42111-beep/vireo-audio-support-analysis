"""
validate_pipeline.py
====================
Full validation of all outputs. Run after compute_agent_metrics.py and
rank_bottom_10.py to confirm correctness.
"""

import hashlib, pathlib, pandas as pd, numpy as np, sys

errors = []
warnings = []

def check(condition, msg, warning=False):
    if not condition:
        if warning:
            warnings.append(msg)
        else:
            errors.append(msg)

SEP = "=" * 70

# ── 1. Original files unchanged ───────────────────────────────────────────────
print(SEP)
print("1. ORIGINAL FILE INTEGRITY (SHA-256)")
print(SEP)

EXPECTED_HASHES = {
    "ef56a2c7-7840-454e-ab7e-a0df87b90bc5-tickets.csv":   "CD5FD9BB8883F26B1CF7932DCA9C0770C67D01EA22ECD456571DDF8CA5400D1B",
    "8fb10115-c45d-42dc-9e04-95154d9c3e41-agents.csv":    "7A396590C585FDF0D36120C9240208E834C5BC6B1039CD7AD0FB01E1C05DF1A2",
    "6990ae61-2433-405d-a790-24fda9cb7743-orders.csv":    "BF399F4FBCD067EC4515618543BD500EDE6CB36BED1AADEF9219B9565BE7A240",
    "1e2a735c-5a79-4c67-9fc0-e0006ea2b76a-customers.csv": "91EE520527A7E80BDD7EA286E621EAAB219B79028D4252FA66A2AC52F759F9BF",
    "c59ac66f-a215-4a8a-8dfe-39fc4db60f5c-products.csv":  "E81B4A60E0D3B37FCB9580FE5B0221667541C3FE38BEFF11E0EE37A3FD0A48D8",
    "support.pdf":                                         "C1778EC66E5895786A451615C91E61FB53FD81B58BD8DE09CD5D3B63B24A10CF",
}
for fname, exp in EXPECTED_HASHES.items():
    actual = hashlib.sha256(pathlib.Path(fname).read_bytes()).hexdigest().upper()
    ok = actual == exp
    print(f"  {'OK  ' if ok else 'FAIL'}  {fname}")
    check(ok, f"File modified: {fname}")

# ── 2. Load outputs ───────────────────────────────────────────────────────────
print()
print(SEP)
print("2. OUTPUT FILE STRUCTURE")
print(SEP)

m = pd.read_csv("agent_metrics.csv")
b = pd.read_csv("bottom_10_agents.csv")
print(f"  agent_metrics.csv:     {len(m)} rows x {len(m.columns)} cols")
print(f"  bottom_10_agents.csv:  {len(b)} rows x {len(b.columns)} cols")

check(len(m) == 44, f"agent_metrics.csv: expected 44 rows, got {len(m)}")
check(len(b) == 10, f"bottom_10_agents.csv: expected 10 rows, got {len(b)}")
check(len(m.columns) == 20, f"agent_metrics.csv: expected 20 cols, got {len(m.columns)}")
check(len(b.columns) == 26, f"bottom_10_agents.csv: expected 26 cols, got {len(b.columns)}")

# ── 3. All agent IDs present ──────────────────────────────────────────────────
print()
print(SEP)
print("3. AGENT ID COVERAGE")
print(SEP)

agents = pd.read_csv("8fb10115-c45d-42dc-9e04-95154d9c3e41-agents.csv")
roster_ids = set(agents["agent_id"])
metrics_ids = set(m["agent_id"])
bottom_ids  = set(b["agent_id"])

missing_in_metrics = roster_ids - metrics_ids
extra_in_metrics   = metrics_ids - roster_ids
print(f"  Roster agents:          {len(roster_ids)}")
print(f"  In agent_metrics.csv:   {len(metrics_ids)}")
print(f"  Missing from metrics:   {sorted(missing_in_metrics)}")
print(f"  Extra in metrics:       {sorted(extra_in_metrics)}")
check(not missing_in_metrics, f"Missing agent IDs in metrics: {missing_in_metrics}")
check(not extra_in_metrics,   f"Extra agent IDs in metrics:   {extra_in_metrics}")

print(f"  Bottom-10 agent IDs: {sorted(bottom_ids)}")
check(bottom_ids.issubset(roster_ids), "Bottom-10 contains unknown agent IDs")
check(len(bottom_ids) == 10, f"Bottom-10 has {len(bottom_ids)} unique IDs (expected 10)")

# ── 4. Tier 2 not in bottom-10 ────────────────────────────────────────────────
print()
print(SEP)
print("4. TIER SEPARATION")
print(SEP)

# bottom_10_agents.csv has no tier column; join from agent_metrics to check
b_with_tier = b.merge(m[["agent_id","tier"]], on="agent_id", how="left")
tier2_in_bottom = b_with_tier[b_with_tier["tier"] == 2]
print(f"  Tier 2 agents in bottom_10_agents.csv: {len(tier2_in_bottom)}")
check(len(tier2_in_bottom) == 0, "Tier 2 agents found in bottom-10 ranking")

tier_dist = m.groupby("tier").size()
print(f"  Tier distribution in agent_metrics.csv: {dict(tier_dist)}")
check(tier_dist.get(1, 0) == 38, f"Expected 38 Tier 1 agents, got {tier_dist.get(1,0)}")
check(tier_dist.get(2, 0) == 6,  f"Expected 6 Tier 2 agents, got {tier_dist.get(2,0)}")

# ── 5. Ticket count reconciliation ────────────────────────────────────────────
print()
print(SEP)
print("5. TICKET COUNT RECONCILIATION")
print(SEP)

tickets = pd.read_csv("ef56a2c7-7840-454e-ab7e-a0df87b90bc5-tickets.csv", low_memory=False)
total_in_file  = len(tickets)
total_in_metrics = m["total_tickets"].sum()
print(f"  Tickets in CSV:                  {total_in_file:,}")
print(f"  Sum of total_tickets in metrics: {total_in_metrics:,}")
check(total_in_file == total_in_metrics,
      f"Ticket count mismatch: CSV={total_in_file}, metrics sum={total_in_metrics}")

res_in_file = tickets["status"].isin(["resolved","closed"]).sum()
res_in_metrics = m["resolved_closed_volume"].sum()
print(f"  Resolved/closed in CSV:          {res_in_file:,}")
print(f"  Sum of resolved_closed_volume:   {res_in_metrics:,}")
check(res_in_file == res_in_metrics,
      f"Resolved count mismatch: CSV={res_in_file}, metrics sum={res_in_metrics}")

# ── 6. CSAT validation ────────────────────────────────────────────────────────
print()
print(SEP)
print("6. CSAT VALIDATION")
print(SEP)

for col in ["created_at","first_response_at","resolved_at"]:
    tickets[col] = pd.to_datetime(tickets[col])

csat_expected = tickets[
    tickets["status"].isin(["resolved","closed"]) & tickets["csat_score"].notna()
]
csat_in_csv = len(csat_expected)
csat_in_metrics = m["csat_response_count"].sum()
print(f"  Valid CSAT rows in CSV:           {csat_in_csv:,}")
print(f"  Sum of csat_response_count:       {csat_in_metrics:,}")
check(csat_in_csv == csat_in_metrics,
      f"CSAT count mismatch: CSV={csat_in_csv}, metrics={csat_in_metrics}")

# No zero scores that were actually blank
zero_csat_check = tickets[tickets["csat_score"] == 0]
print(f"  Tickets with csat_score=0 (should be 0): {len(zero_csat_check)}")
check(len(zero_csat_check) == 0, "csat_score=0 found — blanks may have been imputed as zero")

# ── 7. Handle time validation ─────────────────────────────────────────────────
print()
print(SEP)
print("7. HANDLE TIME VALIDATION")
print(SEP)

tickets["handle_mins"] = (
    pd.to_datetime(tickets["resolved_at"]) - pd.to_datetime(tickets["first_response_at"])
).dt.total_seconds() / 60

ht_expected = tickets[
    tickets["status"].isin(["resolved","closed"]) & (tickets["handle_mins"] >= 0)
]
ht_in_csv = len(ht_expected)
ht_in_metrics = m["handle_time_valid_count"].sum()
print(f"  Valid handle-time rows in CSV:     {ht_in_csv:,}")
print(f"  Sum of handle_time_valid_count:    {ht_in_metrics:,}")
check(ht_in_csv == ht_in_metrics,
      f"Handle time count mismatch: CSV={ht_in_csv}, metrics={ht_in_metrics}")

neg_ht_legacy = tickets[
    (tickets["source_system"] == "legacy_fd") & (tickets["handle_mins"] < 0)
]
neg_excluded_in_metrics = m["flag_legacy_handle_excluded"].sum()
print(f"  Negative legacy HT in CSV:         {len(neg_ht_legacy):,}")
print(f"  Sum of flag_legacy_handle_excluded:{int(neg_excluded_in_metrics):,}")
check(len(neg_ht_legacy) == neg_excluded_in_metrics,
      f"Legacy exclusion mismatch: CSV={len(neg_ht_legacy)}, metrics={neg_excluded_in_metrics}")

# ── 8. SLA validation ─────────────────────────────────────────────────────────
print()
print(SEP)
print("8. SLA VALIDATION")
print(SEP)

SLA = {"chat": 15, "email": 480, "voice": 120, "social": 240}
tickets["frt_mins"] = (
    pd.to_datetime(tickets["first_response_at"]) - pd.to_datetime(tickets["created_at"])
).dt.total_seconds() / 60
tickets["sla_target"] = tickets["channel"].map(SLA)
tickets["is_breach"] = tickets["frt_mins"] > tickets["sla_target"]

total_breach_csv = tickets["is_breach"].sum()
total_breach_metrics = m["sla_breach_count"].sum()
print(f"  Total SLA breaches in CSV:         {int(total_breach_csv):,}")
print(f"  Sum of sla_breach_count:           {int(total_breach_metrics):,}")
check(total_breach_csv == total_breach_metrics,
      f"SLA breach mismatch: CSV={total_breach_csv}, metrics={total_breach_metrics}")

# ── 9. Q3 date consistency ────────────────────────────────────────────────────
print()
print(SEP)
print("9. Q3 DATE RANGE CONSISTENCY")
print(SEP)

q3_start = pd.Timestamp("2025-07-01")
q3_end   = pd.Timestamp("2025-09-30 23:59:59")
q3 = tickets[(tickets["created_at"] >= q3_start) & (tickets["created_at"] <= q3_end)]
print(f"  Q3 2025 (Jul-Sep): {len(q3):,} tickets")
print(f"  Source split: legacy_fd={(q3['source_system']=='legacy_fd').sum():,}  helpdesk={(q3['source_system']=='helpdesk').sum():,}")
check(len(q3) > 0, "No Q3 tickets found")
check(len(q3) == 1577, f"Q3 ticket count changed: expected 1577, got {len(q3)}")

# ── 10. Bottom-10 rank reconciliation ─────────────────────────────────────────
print()
print(SEP)
print("10. BOTTOM-10 RECONCILIATION WITH AGENT METRICS")
print(SEP)

b_check = b.merge(m[["agent_id","csat_mean","sla_breach_rate","handle_time_mean_mins"]],
                  on="agent_id", suffixes=("_b","_m"))
csat_ok  = (b_check["csat_mean_b"] - b_check["csat_mean_m"]).abs().max() < 0.001
sla_ok   = (b_check["sla_breach_rate_b"] - b_check["sla_breach_rate_m"]).abs().max() < 0.0001
ht_ok    = (b_check["handle_time_mean_mins_b"] - b_check["handle_time_mean_mins_m"]).abs().max() < 0.01
print(f"  CSAT values match agent_metrics:         {'YES' if csat_ok  else 'NO'}")
print(f"  SLA breach rates match agent_metrics:    {'YES' if sla_ok   else 'NO'}")
print(f"  Handle times match agent_metrics:        {'YES' if ht_ok    else 'NO'}")
check(csat_ok,  "CSAT values in bottom_10 do not match agent_metrics")
check(sla_ok,   "SLA breach rates in bottom_10 do not match agent_metrics")
check(ht_ok,    "Handle times in bottom_10 do not match agent_metrics")

# ── Final result ──────────────────────────────────────────────────────────────
print()
print(SEP)
print("VALIDATION RESULT")
print(SEP)
if errors:
    print(f"  FAILED: {len(errors)} error(s)")
    for e in errors:
        print(f"    ERROR: {e}")
else:
    print(f"  PASSED: all checks passed")
if warnings:
    print(f"  WARNINGS: {len(warnings)}")
    for w in warnings:
        print(f"    WARN:  {w}")
print(SEP)
sys.exit(1 if errors else 0)
