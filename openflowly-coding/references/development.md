# Intent: Requirement Research & Implementation (`build`)

Expert lens: 资深工程师 / senior engineer. When the user gives a concrete requirement/bug/integration directly, research the mainstream approach and official conventions first, get plan approval, then implement elegantly and simply.

## Dependency

Requires the **anysearch** skill for the research step (`$CODEX_HOME/skills/anysearch` or `~/.agents/skills/anysearch`). If missing, stop and ask the user to install it via `skill-installer` first. Do not present guessed "official" specs as if searched.

## Step 1 — Understand & locate

Restate the requirement and acceptance criteria; identify the affected files/modules in the current project and the project's existing stack/version (read package manifests/config rather than assuming). If the request is unclear in a way that changes the design, ask one focused question.

## Step 2 — Research mainstream practice & official specs (anysearch)

Search for and open the authoritative sources:

- How comparable mainstream products/feature libraries solve it (common patterns, edge cases, accessibility, i18n, performance).
- The **official docs/specs** for the exact framework/library/runtime version in use (component API, hooks/lifecycle, theming, platform constraints).
- Recommended libraries only when a well-maintained one is clearly better than hand-rolling; prefer what the project already depends on.

Capture concrete findings with source URLs. Note version-specific breaking details and any mismatch between blog tutorials and current official guidance.

## Step 3 — Propose and wait for confirmation

Present a concise plan for approval:

- Recommended approach and why (mainstream + fits the codebase).
- Files to change/add, key data/state design, and the chosen component/library.
- Key spec points followed, edge cases/empty/loading/error states, and how it will be verified.
- Alternatives briefly considered and rejected.

Wait for explicit user confirmation. Do not start writing the feature before approval (trivial, clearly-scoped bug fixes the user already asked to just apply are exempt).

## Step 4 — Implement elegantly and simply

After approval:

- Match existing code style, naming, and project conventions; integrate with the current architecture, do not introduce a parallel pattern.
- Minimal, readable implementation — no premature abstraction layers, no unnecessary state libraries, no heavy dependencies for a small task, no visual炫技/animation for its own sake.
- Reuse existing components/utilities; handle loading/empty/error and basic validation where relevant; keep accessibility and responsive behavior consistent with the app.
- Keep changes scoped to the requirement; do not refactor unrelated code.

## Step 5 — Verify and report

Run the project's existing lint/typecheck/test/build and any quick manual verification feasible. Report what changed (files), how to test, and any follow-ups. If a verification command cannot run, say so honestly rather than claiming success.
