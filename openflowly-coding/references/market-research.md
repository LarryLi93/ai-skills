# Intent: Market Research (`research`)

Expert lens: 市场研究分析师 / industry analyst. Deliver an evidence-based market study with a visualized HTML report. Do not invent statistics.

## Inputs to confirm

- Product/domain scope and geography (e.g. 中国大陆 / 全球).
- Time horizon for sizing (current year + 3–5 year forward).
- Any known competitors or reference products.

If the product idea is too vague to scope (no clear category), ask one question to pin the category and geography before searching. Otherwise proceed and state assumptions.

## Dependency

Requires the **anysearch** skill (`$CODEX_HOME/skills/anysearch` or `~/.agents/skills/anysearch`). If not installed, stop and tell the user to install it via `skill-installer` before continuing. Do not estimate a market from memory as if it were sourced data.

## Search plan

Run parallel/searches with anysearch across these clusters, then extract the strongest sources (official statistics, analyst reports, listed-company filings, reputable trade bodies, primary surveys):

1. Market size & spending: “<category> 市场规模”, “TAM/SAM/SOM”, “market size”, “CAGR / 年复合增长率”, “行业报告 <year>”.
2. Growth drivers & policy: adoption drivers, regulation, technology shifts, funding.
3. Competitors & pricing: 3–6 representative players, business model, price band, positioning.
4. Audience & demographics: gender split, age-band split, tier-city/region, occupation/income, usage scenario, channels. Prefer surveys/reports that report percentages and sample size.
5. Trends & risks: near-term trends, substitutes, regulatory/macroeconomic risks.

Prefer recent (< 24 months) and primary/authoritative sources. For conflicting figures, report the **range**, name the sources, and pick a clearly-labeled base/central estimate for charts.

## Required report sections

1. 摘要 / Executive summary — 3–5 bullets, conclusion first.
2. 市场定义与边界 — what is in/out of scope; TAM / SAM / SOM.
3. 市场规模 — current size (currency + unit), with low/base/high where data varies; cite source per figure.
4. 年增速范围 — state a CAGR range (e.g. 12%–18%) over the horizon, with driver justification; show a size projection band.
5. 竞争格局 — comparison table of representative players (positioning, audience, pricing, strength/weakness).
6. 人群画像 (audience profile):
   - 各性别占比 (% female / male / other) as a chart.
   - 各年龄段占比 (bands such as ≤18 / 19–24 / 25–30 / 31–40 / 41+) as a chart.
   - Region/tier-city, occupation/income, spending power where available.
   - 典型使用故事 — 2–4 persona stories in JTBD form: who, situation, trigger, goal, how the product is used, success outcome.
7. 驱动因素与趋势.
8. 风险与避雷 — demand, regulatory, competitive, substitution risks.
9. 对该产品的启示 — 3–6 actionable implications (entry wedge, positioning, audience priority, monetization).
10. 数据来源 — numbered source list with name + URL + accessed date.

## HTML visualization

Produce one self-contained `market-research.html` under a product folder such as `<workspace>/<product-slug>/01-market-research/`. Requirements:

- Inline CSS/JS; render charts with inline SVG or lightweight canvas/JS you write yourself (assume no CDN at view time). Prefer clear, labeled bars/donuts/lines over decoration.
- Must include at minimum: TAM/SAM/SOM or market-size visual, growth/projection band chart, gender donut, age-band bar chart, competitor comparison table, persona story cards.
- Show data ranges and source footnotes on figures. Chinese UI labels; numbers formatted with units.
- Responsive 9:16-friendly and desktop readable. Save the file, then open/show it to the user and summarize the headline findings in chat.

## Sourcing honesty

Every quantitative claim needs a source; where data is an analyst estimate or triangulation, label it 估算 and explain the basis. If a required demographic split genuinely cannot be sourced, say “数据不足” and present a qualitative read rather than fabricating percentages.
