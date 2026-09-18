# Intent: Product Roadmap (`roadmap`)

Expert lens: 产品负责人 / head of product. Turn the confirmed information architecture into a phased, outcome-driven roadmap and visualize it.

## Prerequisite gate

Requires a completed **information architecture** artifact in this product thread. If absent, stop and run/request `ia` first (see SKILL.md stage dependencies). Build directly on the confirmed tiered capabilities; do not invent new scope without flagging it.

## Planning logic

1. Take the IA capabilities and sequence them by: user value to the core wedge, dependency order, build effort, risk/uncertainty, and data needed before later features make sense.
2. Define phases (recommend, do not blindly follow):
   - **MVP / P0 (v1.0)** — differentiators made usable + the minimum table stakes needed for them to work. Ship value, not a feature list.
   - **P1 (v1.x)** — retention & habit loops, essential personalization/content depth, key integrations.
   - **P2 / v2** — growth, social/community or advanced features, monetization expansion, platform expansion.
   - Explicitly exclude 避雷 items; park 非必要 items in a labeled backlog with revisit triggers.
3. For each phase give: goal/outcome (not just features), included capabilities (link to IA modules), key milestones/exit criteria, rough effort band (S/M/L or weeks for a small team), and dependencies/risks.
4. State assumptions about team size/cadence, and keep the plan revisable.

## Deliverable

Single self-contained `roadmap.html` under `<workspace>/<product-slug>/03-roadmap/`, containing:

- A visual timeline / swimlane or gantt-style chart (inline SVG/CSS) across MVP→P1→P2, with milestone markers and dependency hints.
- Per-phase cards: outcome, capabilities, exit criteria, effort band, risks.
- A prioritization matrix (impact vs effort) for the differentiator capabilities.
- A “暂不做 / backlog” section carrying IA 避雷 and deferred items with revisit conditions.

Save, open/show it, and summarize the MVP scope in chat. End by confirming the roadmap — confirmation (and this artifact) is the prerequisite for the UI design stage.
