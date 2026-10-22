---
name: vue-optimize
description: Analyzes Vue 3 component structure and suggests optimizations for performance and code reuse. Reports oversized components, duplicated markup/CSS/logic across views, reactivity and rendering inefficiencies, and extraction candidates for components and composables. Analysis only; it does not modify files unless the user asks to apply a suggestion. Invoke when the user asks to review Vue components, find duplication, improve performance, refactor for reuse, or optimize the frontend.
---

# Vue Optimize

Analyze the Vue 3 frontend and produce a prioritized, evidence-based list of performance and code-reuse improvements. This skill is read-only by default.

## Scope

- Target: the paths the user names. If none, analyze all of `client/src/` (`views/`, `components/`, `App.vue`, `api.js`, `main.js`).
- Skip `node_modules/` and build output.
- Do not edit anything during analysis. Applying a suggestion is a separate step the user must ask for.

## Phase 1: Inventory

Use the Explore subagent (or Bash) to collect facts before forming opinions.

1. **Size and shape** per `.vue` file: total lines, and the line split between `<template>`, `<script setup>`, and `<style>`.
   ```bash
   wc -l client/src/views/*.vue client/src/components/*.vue client/src/App.vue
   ```
2. **Imports and usage**: which components each file imports and renders; which components are used in only one place.
3. **API usage**: every `api.*` call in `client/src/api.js` consumers, and which view calls it (look for the same call made from multiple views or components).
4. **Routes**: the route list in `main.js`, to see which views are eagerly imported.

## Phase 2: Detect issues

Check each category below. For every finding, record `file:line`, a one-line evidence snippet, and the impact. Do not report a pattern you did not actually see in the code.

### Performance

- **Eager route imports**: views imported statically in `main.js` instead of `() => import(...)`. Large views (Dashboard, Spending) are the best candidates for lazy loading.
- **Work in templates**: function calls, `.filter()`, `.map()`, `.reduce()`, `.sort()`, or `new Date()` inside `<template>` expressions that re-run every render. Suggest `computed`.
- **Computed that should be cached or is mutating**: `.sort()` on a ref array inside a computed (mutates source; use `[...arr].sort()`), computeds that recompute large lists from several unrelated sources.
- **Over-broad reactivity**: large arrays or API payloads held in `ref` where `shallowRef` is enough (data replaced wholesale, never mutated in place).
- **Watchers**: `watch` with `deep: true` on large objects; watchers that only derive a value (should be `computed`); several watchers triggering several separate fetches when one combined call would do.
- **Duplicate fetching**: the same endpoint called by multiple views on mount with identical filters, or re-fetched on every filter change when only a subset of data depends on that filter.
- **Rendering cost**: long `v-for` lists without pagination or virtualization; `v-for` keyed by `index` (project rule: key by `sku`, `month`, etc.); `v-if` and `v-for` on the same element; heavy components that could use `v-once` or `v-memo`.
- **Modal components**: modals mounted permanently with `v-show` instead of `v-if`, or loaded eagerly though rarely opened (candidates for `defineAsyncComponent`).
- **Custom SVG charts**: coordinate or path math recomputed in the template instead of a computed.
- **Safety checks that also cost time**: `.getMonth()` or date parsing repeated per row without validating the date once (project rule: validate dates before `.getMonth()`).

### Code reuse

- **Duplicated template blocks**: near-identical markup across views (stat cards, tables, status badges, empty/loading/error states, modal shells, filter-driven headers). Candidate for a shared component with props and slots.
- **Duplicated script logic**: the same loading/error handling, filter wiring, formatting helpers (currency, dates, percentages), or status-to-color mapping repeated in several files. Candidates for composables (`client/src/composables/`) or a utils module.
- **Duplicated CSS**: the same rule sets in multiple `<style>` blocks, or classes that belong in the shared styles in `App.vue`. Compare class names across files, not only identical text.
- **Prop drilling and event chains**: values passed through more than two component levels; suggest `provide`/`inject` or a small shared store only if it removes real complexity.
- **God components**: files with more than roughly 400 lines or several unrelated responsibilities (data fetching, filtering, formatting, chart drawing, and modal state in one file). Propose a split along responsibility lines.
- **Dead code**: unused imports, refs, computeds, props, and CSS classes.

## Phase 3: Rank

Score each finding:

- **Impact**: High (visible slowness, large bundle, or removes 100+ duplicated lines), Medium, Low.
- **Effort**: Small (under 30 minutes, local change), Medium, Large (touches many files).
- **Risk**: Low, Medium, High (changes behavior or shared layout).

Order by impact first, then lower effort. Merge findings that share a fix (for example, one shared `StatCard` component resolving duplication in five views).

## Phase 4: Report

Output in this structure. Keep it concise; no emojis.

```
## Summary
Files analyzed: N | Findings: N (High: n, Medium: n, Low: n)
Biggest wins: 1-3 bullets.

## Performance
### 1. <title>  [Impact: High | Effort: Small | Risk: Low]
- Where: client/src/views/X.vue:123, Y.vue:45
- Evidence: `<snippet>`
- Why it matters: <one sentence>
- Suggested fix: <concrete change, with a short code sketch if helpful>

## Code reuse
### 1. ...

## Suggested extractions
| New unit | Type (component/composable/util) | Replaces | Files affected |

## Not worth changing
Patterns that look suspect but are fine here, with a reason.
```

End with a recommended order of work and ask which items to apply.

## Applying suggestions

Only after the user picks items:

- Any creation or significant modification of a `.vue` file MUST be delegated to the **vue-expert** subagent (project rule). Give it the finding, the exact files, and the expected behavior to preserve.
- After changes, run the **code-reviewer** subagent on the diff.
- Verify in the browser with Playwright (`http://localhost:3000`): load each affected page and check for console errors and visual regressions.
- Follow project conventions: unique `v-for` keys, Composition API, slate/gray design tokens, no emojis in the UI, and comments on any non-obvious logic change.
- Make changes in small, separate commits per finding so each can be reverted alone.

## Guardrails

- Prefer the simplest fix. Do not recommend a state library, a component framework, or a rewrite for a problem that a computed or a shared component solves.
- Do not suggest abstractions for code that appears only twice unless the duplication is large and likely to diverge in a harmful way.
- Never change the data contract with the backend as part of a frontend optimization. If a Pydantic model or JSON shape would need to change, flag it separately.
- If a metric cannot be measured from source (real render time, bundle size), say so and suggest how to measure it (Vue DevTools profiler, `vite build` output) instead of guessing numbers.
