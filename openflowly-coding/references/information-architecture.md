# Intent: Product Information Architecture (`ia`)

Expert lens: 资深产品架构师 / information architect. Co-create the product's capability set with the user, tier every capability, and deliver an information-architecture diagram.

## Workflow

1. Confirm the product's one-line definition, target users (reuse prior market-research persona findings if present), platform, and core value proposition. If these are unknown, ask the few questions needed, or proceed on stated assumptions and label them.
2. Brainstorm capabilities with the user. Propose a complete candidate list organized by user journey / object domain, and invite additions/removals. Do not lock the set unilaterally — this is an alignment step.
3. Classify each capability into one tier (see below) and show the reasoning in one line each.
4. Confirm the tiered capability set with the user before finalizing the diagram.
5. Produce the IA artifact (diagram + spec) as self-contained HTML.

## Capability tiers

Tag every capability with exactly one tier and a short rationale:

- 大众化功能 (baseline / table stakes) — users expect it in this category; omitting it hurts trust (e.g. login, search, content detail, basic settings).
- 差异化功能 (differentiator) — the core reason to choose this product; tied directly to the value proposition and persona JTBD. This is where focus should be.
- 非必要功能 (optional / later) — real value but not needed for the target wedge; candidate for later phases or power users.
- 避雷功能 (avoid / anti-pattern) — explicitly recommend NOT building now: feature-factory bloat, high cost / low frequency, legal/privacy risk, dark patterns, over-personalization before data exists, social features with no graph, etc. Say why and under what future condition it could be revisited.

Keep 大众化 and 差异化 honest: not everything is a differentiator. A healthy v1 has a small, sharp differentiator set.

## IA structure

Organize capabilities into top-level modules/tabs, with:

- Module → page/section → key components/actions.
- Core content objects and their relationships (e.g. 文章 → 收藏/进度/笔记；课程 → 章节 → 学习记录).
- Primary navigation (tabs) vs. secondary entry points.
- The differentiator modules visually highlighted; 避雷 items shown in a distinct “建议暂不做” panel.

## Deliverable

Single self-contained `information-architecture.html` under `<workspace>/<product-slug>/02-ia/`, containing:

- A hierarchical IA tree diagram (inline SVG/CSS, no CDN dependency for the core view), with tier color coding and a legend.
- A capability table: capability | tier | rationale | target phase hint.
- A “建议避雷/暂不做” panel with reasons and revisit conditions.
- Open questions / decisions for the user.

Save, open/show it, and end by asking the user to confirm the IA — this confirmation feeds the Roadmap stage. If the user then asks for a roadmap, proceed using this artifact.
