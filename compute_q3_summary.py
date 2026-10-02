"""
compute_q3_summary.py
=====================
Computes Q3 business-level summary statistics and cost / replacement analyses.
All figures are printed for use in the final deliverables.

Q3 DEFINITION
-------------
The assessment brief states this is a Q3 training review.
The ticket window spans 2025-01-01 to 2026-06-30.
Standard Indian fiscal year quarters:
  Q1: Apr-Jun  |  Q2: Jul-Sep  |  Q3: Oct-Dec  |  Q4: Jan-Mar

However, the data window is calendar-year Jan 2025 - Jun 2026, and the
assessment brief says "Q3 training review" without specifying a fiscal year.
The most recent complete quarter fully contained in the data is:
  Q4 FY25 / Calendar Q1 2026: Jan-Mar 2026
  Q3 FY26 / Calendar Q4 2025: Oct-Dec 2025

Given the data runs Jan 2025 - Jun 2026 and the brief says Q3, the most
defensible interpretation is CALENDAR Q3 2025 = July-September 2025, which
is the last complete calendar quarter before the system cut-over AND fully
within the data window.  However, Q4 calendar 2025 (Oct-Dec 2025, after the
helpdesk cut-over) is also a complete quarter.

We compute BOTH and report clearly.  The analysis uses ALL data for
agent-level metrics (maximising sample size per agent) and uses
calendar-quarter filtering only for the business summary.
"""

import pandas as pd
import numpy as np

TICKETS  = "ef56a2c7-7840-454e-ab7e-a0df87b90bc5-tickets.csv"
AGENTS   = "8fb10115-c45d-42dc-9e04-95154d9c3e41-agents.csv"
ORDERS   = "6990ae61-2433-405d-a790-24fda9cb7743-orders.csv"
PRODUCTS = "c59ac66f-a215-4a8a-8dfe-39fc4db60f5c-products.csv"

tickets  = pd.read_csv(TICKETS, low_memory=False)
agents   = pd.read_csv(AGENTS)
orders   = pd.read_csv(ORDERS)
products = pd.read_csv(PRODUCTS)

for col in ["created_at", "first_response_at", "resolved_at"]:
    tickets[col] = pd.to_datetime(tickets[col])
orders["order_date"] = pd.to_datetime(orders["order_date"])
products["launch_date"] = pd.to_datetime(products["launch_date"])

# ── SLA targets ───────────────────────────────────────────────────────────────
SLA = {"chat": 15, "email": 480, "voice": 120, "social": 240}
tickets["frt_mins"] = (tickets["first_response_at"] - tickets["created_at"]).dt.total_seconds() / 60
tickets["handle_mins"] = (tickets["resolved_at"] - tickets["first_response_at"]).dt.total_seconds() / 60
tickets["sla_target"] = tickets["channel"].map(SLA)
tickets["is_breach"] = tickets["frt_mins"] > tickets["sla_target"]
tickets["is_resolved_closed"] = tickets["status"].isin(["resolved", "closed"])

# Valid handle time: non-negative, resolved/closed only
tickets["ht_valid"] = tickets["is_resolved_closed"] & (tickets["handle_mins"] >= 0)

SEP = "=" * 70

# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("1. DATE RANGE AND Q3 ANALYSIS")
print(SEP)

print(f"Full dataset range: {tickets['created_at'].min().date()} to {tickets['created_at'].max().date()}")
print(f"Total tickets in dataset: {len(tickets):,}")

# Calendar quarters present in data
for label, start, end in [
    ("Cal Q3 2025 (Jul-Sep 2025)", "2025-07-01", "2025-09-30"),
    ("Cal Q4 2025 (Oct-Dec 2025)", "2025-10-01", "2025-12-31"),
    ("Cal Q1 2026 (Jan-Mar 2026)", "2026-01-01", "2026-03-31"),
    ("Cal Q2 2026 (Apr-Jun 2026)", "2026-04-01", "2026-06-30"),
]:
    s, e = pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta("23:59:59")
    sub = tickets[(tickets["created_at"] >= s) & (tickets["created_at"] <= e)]
    print(f"  {label}: {len(sub):,} tickets")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("2. FULL-DATASET SUMMARY (all 18-month window, used for agent metrics)")
print(SEP)

total = len(tickets)
res_closed = tickets["is_resolved_closed"].sum()
csat_valid = tickets[tickets["is_resolved_closed"] & tickets["csat_score"].notna()]
ht_valid_tk = tickets[tickets["ht_valid"]]
breaches = tickets["is_breach"].sum()

print(f"Total tickets:             {total:,}")
print(f"Resolved/closed:           {res_closed:,}  ({res_closed/total*100:.1f}%)")
print(f"Open/pending:              {total - res_closed:,}")
print(f"CSAT responses (non-null): {len(csat_valid):,}")
print(f"CSAT response rate:        {len(csat_valid)/total*100:.1f}%")
print(f"Average CSAT:              {csat_valid['csat_score'].mean():.4f}")
print(f"CSAT distribution:")
for v in [1,2,3,4,5]:
    n = (csat_valid["csat_score"] == v).sum()
    print(f"   {v}: {n:,}  ({n/len(csat_valid)*100:.1f}%)")
print(f"Valid handle-time records: {len(ht_valid_tk):,}")
print(f"Mean handle time (valid):  {ht_valid_tk['handle_mins'].mean():.1f} min  ({ht_valid_tk['handle_mins'].mean()/60:.2f} hrs)")
print(f"Median handle time:        {ht_valid_tk['handle_mins'].median():.1f} min")
print(f"SLA breaches:              {breaches:,}  ({breaches/total*100:.1f}%)")
print(f"  by channel:")
for ch in ["chat", "email", "voice", "social"]:
    sub = tickets[tickets["channel"] == ch]
    b = sub["is_breach"].sum()
    print(f"    {ch:8s}: {b:,} / {len(sub):,}  ({b/len(sub)*100:.1f}%)  target={SLA[ch]} min")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("3. Q3 WINDOW SUMMARY (Cal Q3 2025: Jul 1 - Sep 30 2025)")
print(SEP)

q3_start = pd.Timestamp("2025-07-01")
q3_end   = pd.Timestamp("2025-09-30 23:59:59")
q3 = tickets[(tickets["created_at"] >= q3_start) & (tickets["created_at"] <= q3_end)].copy()

q3_res_closed = q3["is_resolved_closed"].sum()
q3_csat = q3[q3["is_resolved_closed"] & q3["csat_score"].notna()]
q3_ht = q3[q3["ht_valid"]]
q3_breach = q3["is_breach"].sum()

print(f"Q3 date range used:        2025-07-01 to 2025-09-30")
print(f"Source system split:       legacy_fd={( q3['source_system']=='legacy_fd').sum():,}  helpdesk={(q3['source_system']=='helpdesk').sum():,}")
print(f"Total Q3 tickets:          {len(q3):,}")
print(f"Resolved/closed:           {q3_res_closed:,}  ({q3_res_closed/len(q3)*100:.1f}%)")
print(f"CSAT response rate:        {len(q3_csat)/len(q3)*100:.1f}%")
print(f"Average CSAT (Q3):         {q3_csat['csat_score'].mean():.4f}")
print(f"Valid handle-time records: {len(q3_ht):,}")
q3_neg_ht = q3[q3["is_resolved_closed"] & (q3["handle_mins"] < 0)]
print(f"  (legacy neg excluded):   {len(q3_neg_ht):,}")
print(f"Mean handle time (valid):  {q3_ht['handle_mins'].mean():.1f} min")
print(f"SLA breach rate (Q3):      {q3_breach/len(q3)*100:.1f}%  ({q3_breach:,} of {len(q3):,})")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("4. CONTACT COST ANALYSIS")
print(SEP)

# Policy cost per contact by channel
COST = {"chat": 210, "email": 260, "voice": 520, "social": 240}
BLENDED = 290
TRANSFER_COST = 305
AGENT_HOUR_COST = 165
SHIFT_HOURS = 8

# Full dataset channel counts
channel_counts = tickets["channel"].value_counts()
print("Channel distribution (full dataset):")
total_cost = 0
for ch, cnt in channel_counts.items():
    cost = cnt * COST[ch]
    total_cost += cost
    print(f"  {ch:8s}: {cnt:,} tickets x Rs{COST[ch]:,} = Rs{cost:,}")
print(f"  Total (sum of per-channel): Rs{total_cost:,}")
blended_total = total * BLENDED
print(f"  Total (blended Rs290):      Rs{blended_total:,}")

# Monthly estimate using 650 tickets/week from brief
WEEKLY = 650
monthly_tickets = WEEKLY * 52 / 12
print(f"\nEstimated monthly tickets (650/wk * 52/12): {monthly_tickets:.0f}")
monthly_cost_blended = monthly_tickets * BLENDED
print(f"Monthly blended contact cost: Rs{monthly_cost_blended:,.0f}")
annual_cost_blended = monthly_cost_blended * 12
print(f"Annual blended contact cost:  Rs{annual_cost_blended:,.0f}")

# Transfer cost from data
hd_transfers = tickets[tickets["source_system"] == "helpdesk"]["transfers"]
total_transfers = hd_transfers.sum()
transfer_cost_total = total_transfers * TRANSFER_COST
print(f"\nHelpdesk transfers recorded: {int(total_transfers):,}")
print(f"Transfer cost (helpdesk only): Rs{transfer_cost_total:,} (Rs{TRANSFER_COST}/transfer)")
print(f"  NOTE: legacy_fd transfers field unreliable; excluded from cost.")

# SLA breach credit cost
SLA_CREDIT = 350
breach_count = int(tickets["is_breach"].sum())
sla_credit_total = breach_count * SLA_CREDIT
print(f"\nSLA breaches in dataset: {breach_count:,}")
print(f"Breach credits issued:   Rs{breach_count:,} x Rs{SLA_CREDIT} = Rs{sla_credit_total:,}")
# Monthly
monthly_breach_rate = tickets["is_breach"].mean()
monthly_breach_credits = monthly_tickets * monthly_breach_rate * SLA_CREDIT
print(f"Monthly breach credits (at {monthly_breach_rate*100:.1f}% rate on {monthly_tickets:.0f} tickets): Rs{monthly_breach_credits:,.0f}")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("5. TRAINING BUDGET ANALYSIS  (Priya's budget: Rs 4,00,000)")
print(SEP)

BUDGET = 400000
N_BOTTOM = 10

equal_per_agent = BUDGET / N_BOTTOM
print(f"Total budget:               Rs{BUDGET:,}")
print(f"Bottom-ten agent count:     {N_BOTTOM}")
print(f"Equal split per agent:      Rs{equal_per_agent:,.0f}")

# Alternative splits
for n, label in [(5,"top-5 priority agents"), (3,"top-3 critical agents"), (10,"all 10"), (7,"7 agents")]:
    amt = BUDGET / n
    print(f"  Split across {n:2d} ({label:28s}): Rs{amt:,.0f} each")

# Budget as % of monthly/annual cost
print(f"\nBudget context:")
print(f"  Rs4,00,000 as % of monthly blended cost:  {BUDGET/monthly_cost_blended*100:.1f}%")
print(f"  Rs4,00,000 as % of annual blended cost:   {BUDGET/annual_cost_blended*100:.2f}%")
print(f"  Rs4,00,000 in agent-hours (Rs165/hr):     {BUDGET/AGENT_HOUR_COST:.0f} agent-hours")
print(f"  Rs4,00,000 in agent-shifts (8hr):         {BUDGET/AGENT_HOUR_COST/SHIFT_HOURS:.0f} agent-shifts")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("6. REPLACEMENT COST ANALYSIS")
print(SEP)

# Policy: replacement cost = unit_cost_inr + 340
LOGISTICS = 340
products["replacement_cost"] = products["unit_cost_inr"] + LOGISTICS

print("Replacement cost by SKU (unit_cost + Rs340 logistics):")
print(products[["sku","product_name","unit_cost_inr","replacement_cost","retail_price_inr"]].to_string(index=False))

# Replacements issued in tickets
replacements = tickets[tickets["replacement_issued"] == "Y"].copy()
print(f"\nTotal replacement_issued=Y tickets: {len(replacements):,}")
print(f"  by source_system:")
print(replacements["source_system"].value_counts().to_string())

# Join to product to get unit cost
rep_with_cost = replacements.merge(
    products[["sku","unit_cost_inr","replacement_cost"]], 
    left_on="product_sku", right_on="sku", how="left"
)
rep_with_cost["rep_cost_used"] = rep_with_cost["replacement_cost"]  # unit_cost + 340

total_rep_cost = rep_with_cost["rep_cost_used"].sum()
mean_rep_cost  = rep_with_cost["rep_cost_used"].mean()
print(f"\nPolicy replacement cost totals:")
print(f"  Total replacement cost (policy formula): Rs{total_rep_cost:,.0f}")
print(f"  Mean replacement cost per ticket:         Rs{mean_rep_cost:,.0f}")
print(f"  Min / Max replacement cost:               Rs{rep_with_cost['rep_cost_used'].min():.0f} / Rs{rep_with_cost['rep_cost_used'].max():.0f}")

print(f"\nReplacement cost by product family:")
rep_by_sku = rep_with_cost.groupby("product_sku").agg(
    count=("ticket_id","count"),
    unit_cost=("unit_cost_inr","first"),
    rep_cost_each=("replacement_cost","first"),
    total_cost=("rep_cost_used","sum")
).sort_values("total_cost", ascending=False)
print(rep_by_sku.to_string())

# Arjun's Rs2500 estimate vs policy
print(f"\nNote on Arjun's Rs2,500 estimate:")
arjun_total = len(replacements) * 2500
print(f"  If Rs2,500 flat used: Rs{arjun_total:,} (NOT the policy cost)")
print(f"  Policy formula total: Rs{total_rep_cost:,.0f}")
print(f"  Difference:           Rs{abs(arjun_total - total_rep_cost):,.0f}")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("7. DUAL-PAYOUT ANOMALIES (refund + replacement on same ticket)")
print(SEP)

dual = tickets[tickets["refund_amount_inr"].notna() & (tickets["replacement_issued"] == "Y")].copy()
dual_with_cost = dual.merge(
    products[["sku","unit_cost_inr","replacement_cost"]], 
    left_on="product_sku", right_on="sku", how="left"
)
dual_with_cost["total_anomaly_cost"] = dual_with_cost["refund_amount_inr"] + dual_with_cost["replacement_cost"]

print(f"Dual-payout tickets: {len(dual_with_cost)}")
print(dual_with_cost[[
    "ticket_id","refund_amount_inr","refund_reason_code",
    "unit_cost_inr","replacement_cost","total_anomaly_cost","source_system"
]].to_string(index=False))
print(f"\nTotal anomalous payout (refund + replacement cost, policy formula): Rs{dual_with_cost['total_anomaly_cost'].sum():,.0f}")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("8. GOODWILL REFUNDS EXCEEDING Rs500 CAP")
print(SEP)

gw = tickets[tickets["refund_reason_code"] == "GW-OTHER"].copy()
gw_over = gw[gw["refund_amount_inr"] > 500]
print(f"Total GW-OTHER tickets: {len(gw)}")
print(f"GW-OTHER refunds > Rs500 cap: {len(gw_over)}  ({len(gw_over)/len(gw)*100:.0f}%)")
print(f"Total excess goodwill paid: Rs{(gw_over['refund_amount_inr'] - 500).sum():,.0f}")
print(f"Mean goodwill refund (all): Rs{gw['refund_amount_inr'].mean():,.0f}")

# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("9. DATA QUALITY SUMMARY TABLE")
print(SEP)

dq_items = [
    ("Legacy negative handle times",
     2309, 2309/len(tickets)*100,
     "ALL legacy_fd; excluded from handle-time means. UTC/IST reconstruction error."),
    ("resolved_at < created_at (legacy)",
     2121, 2121/len(tickets)*100,
     "62.9% of legacy tickets. Same root cause as above."),
    ("CSAT on open/pending tickets",
     249, 249/len(tickets)*100,
     "Excluded from CSAT means; ticket not yet resolved."),
    ("Refund + replacement on same ticket",
     6, 6/len(tickets)*100,
     "Policy violation (section 5). Rs{:,.0f} total anomalous payout.".format(dual_with_cost["total_anomaly_cost"].sum())),
    ("Zero-transfer team mismatches",
     468, 468/len(tickets)*100,
     "327 helpdesk; transfers counter may be under-incremented."),
    ("Ticket created before order date",
     175, 175/len(tickets)*100,
     "67 are >30 days apart; likely wrong order_id linkage."),
    ("Tickets with null order_id",
     4107, 4107/len(tickets)*100,
     "35% of all tickets; includes Delivery & Shipping (667). Limits order analysis."),
    ("Goodwill refunds > Rs500 cap",
     32, 32/37*100,
     "86% of GW-OTHER tickets exceed policy cap without documented approval."),
    ("Tickets before product launch date",
     19, 19/len(tickets)*100,
     "VA-EB-PL2 (16), VA-AC-CASE (2), VA-SP-MINI (1). Minor."),
]

print(f"{'Issue':<42} {'Count':>7} {'%':>6}   {'Business impact'}")
print("-"*110)
for item in dq_items:
    name, count, pct, impact = item
    print(f"{name:<42} {count:>7,} {pct:>5.1f}%   {impact}")
