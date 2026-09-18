# Intent: Product UI Design (`ui`)

Expert lens: 产品设计师 / product designer. Derive the screen set from the roadmap, align on text wireframes, then generate high-fidelity mockups with the openflowly-generate skill.

## Prerequisite gate

Requires a completed **roadmap** (which itself requires information architecture). If absent, stop and request/run the prior stages (see SKILL.md). Scope the UI to the **MVP/P0 screens** unless the user names a phase.

## Dependency: openflowly-generate

Requires the **openflowly-generate** skill (`$CODEX_HOME/skills/openflowly-generate` or `~/.agents/skills/openflowly-generate`).
- If missing: instruct the user to install it via `skill-installer` from `https://github.com/LarryLi93/ai-skills/tree/main/openflowly-generate` (`install-skill-from-github.py --url <url>`); available next turn.
- It needs an Openflowly API key. On first use, guide the user to register at `https://www.openflowly.com`, create a key, and paste it back so the skill configures it. Never echo the key.

## Step 1 — Screen inventory & content (before any image)

From the roadmap MVP, list the screens and their content. For each screen specify: purpose, entry point, key modules/blocks, primary actions, key states (empty / loading / error / data), and navigation. Tie screens to IA modules and the differentiator.

## Step 2 — Plain-text hierarchy sketch (.txt) — requires confirmation

Create `ui-wireframes.txt` under `<workspace>/<product-slug>/04-ui/` containing an ASCII/indented hierarchy sketch for every screen, e.g.:

```
[首页 Home]
├─ 顶部栏: 问候语 · 搜索入口 · 头像
├─ 今日推荐卡片(差异化)
│  ├─ 标题 / 摘要 / 标签
│  └─ 主按钮: 开始阅读
├─ 分类入口横滑
├─ 继续学习列表(进度条)
└─ 底部 Tab: 首页 / 发现 / 收藏 / 我的
   - 状态: 空态/加载/失败说明
```

Show the screen list + txt sketch and **explicitly ask for confirmation**. Do not generate images yet. Capture edits and re-confirm until the user approves.

## Step 3 — Generate 5 variants per page (only after confirmation)

For each confirmed screen, invoke openflowly-generate to create **5 design variants** at **9:16**. Defaults per the skill: model `Gpt Image 2.5`, `resolution=1K`, `quality=low` (do not raise quality unless the user explicitly asks). Distinct variant directions for each page so the user can choose a style, for example: 极简专注 / 年轻社区 / 卡片式 / 深色高级 / 活力渐变.

Build detailed prompts: screen name, layout hierarchy mirroring the txt sketch, target audience (20–30 young users), platform/iOS feel, color & style direction per variant, 9:16, high-fidelity UI mockup, Chinese interface text, no device bezel, no brand logo, no watermark.

Use one openflowly-generate batch (repeated `--prompt`, or `--input-jsonl` for many screens) so outputs land in a single fresh batch folder. Then verify each file exists and is non-empty, and present 5 variants per screen grouped by page with their local absolute paths. State model/ratio/size and confirm no JSON residue. Offer to refine a chosen variant or unify a winning style across screens.
