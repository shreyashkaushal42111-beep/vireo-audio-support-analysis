# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Repository Overview

This is a **data analysis workspace** for Vireo Audio Pvt. Ltd. customer support operations. There is no application code, build system, or test runner. The repository contains five CSV datasets and one policy PDF.

## File Map

| File | Content |
|------|---------|
| `ef56a2c7-…-tickets.csv` | Support tickets (main fact table) |
| `8fb10115-…-agents.csv` | Agent roster (same file exists with and without ` (1)` — identical content) |
| `1e2a735c-…-customers.csv` | Customer master |
| `6990ae61-…-orders.csv` | Order master |
| `c59ac66f-…-products.csv` | Product catalogue |
| `support.pdf` | Operating policy (authoritative rules source) |

## Critical Data Gotchas

### Timestamps
- Ticket `created_at`, `first_response_at`, `resolved_at` exported from the **helpdesk UI are in IST**; API exports are UTC. The CSV files in this repo come from the UI and are **IST**.
- Migrated legacy tickets (`source_system = legacy_fd`) had their `resolved_at` reconstructed from a UTC event log — do not assume consistency with current-system tickets.
- Some `resolved_at` values appear **earlier than** `created_at` for legacy tickets (a known artefact of the UTC-to-IST reconstruction).

### SLA / Breach calculation
- First-response SLA targets differ by channel: **chat 15 min, voice callback 2 h, social 4 h, email 8 h**.
- An SLA breach credit of **Rs 350** is auto-issued; it appears on the P&L, not as a `refund_amount_inr` in the ticket. Do **not** add breach credits to refund sums.
- SLA breach is reported against the **resolving agent** (`agent_id`), not the assigned team.

### Agent Roster
- An agent who changes site or shift receives a **new roster row** with the same `agent_id`. Always filter by `from_date`/`to_date` to get the active assignment at a point in time. `to_date` is blank for current assignments.
- The two agents CSV files (`agents.csv` and `agents (1).csv`) are identical — use either one.

### CSAT
- Blank `csat_score` means **no response** — exclude from averages, never treat as 0.
- Survey response rate is ~45%; averages based on responders only.

### Refunds vs Replacements
- A customer must **never** receive both a refund and a replacement for the same order. If both `refund_amount_inr > 0` and `replacement_issued = Y` on the same ticket it is a data anomaly to flag, not to cost doubly.
- Replacement cost = product `unit_cost_inr` (from products.csv) + **Rs 340** (reverse pickup + forward shipping). Do **not** use `retail_price_inr` for cost modelling.
- Goodwill credits are capped at **Rs 500/ticket** and are separate from refunds; they are not in the tickets CSV.

### Transfers
- `transfers` field counts hand-offs between teams and exists **only for current-system tickets** (`source_system = helpdesk`). Legacy tickets have `transfers = 0` or blank by default — do not compare transfer rates across source systems.
- Internal transfer cost for business cases: **Rs 305 per transfer**.

### Teams & Tiers
- Tier 2 agents (Escalations & Warranty) handle multi-day, multi-touch cases. **Do not compare Tier 2 agents to Tier 1 on volume or tickets-closed metrics.**
- Warranty replacements may only be approved by Tier 2 agents.

### Products
- Accessories (`VA-AC-*`) carry a **6-month warranty**, all other products 12 months.
- `unit_cost_inr` is the planning cost for replacements; `retail_price_inr` is the customer-facing price.
- `VA-EB-PL2` and `VA-AC-CASE` have future `launch_date` values (2025-07-15 / 2025-08-01) — they may appear in orders before their launch dates if data covers a forecast period.

### Cost Standards (FY26 planning)
- Per-contact fully loaded cost: chat Rs 210 · email Rs 260 · voice Rs 520 · social Rs 240 · blended Rs 290.
- Agent cost for staffing: Rs 165/agent-hour; one shift = 8 hours.

## Key Relationships

```
customers  ──< orders  ──< tickets (via order_id)
products   ──< orders  (via sku)
products   ──< tickets (via product_sku)
agents     ──< tickets (via agent_id)
```

- `tickets.agent_id` is the **resolving agent**, not necessarily the initially assigned agent.
- `tickets.assigned_team` is the **first-assigned team**, not the resolving team.
- An agent's active team/shift must be looked up by joining on `agent_id` and checking `from_date ≤ ticket_date ≤ to_date` in the roster.

## Authoritative Policy Reference

All business rules (SLA targets, cost rates, refund codes, team definitions) are in [`support.pdf`](support.pdf). When a question involves policy, cite that document.
