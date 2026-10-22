---
name: saas-redesign
description: Redesigns a Vue 3 application's UI into a modern SaaS-style interface. Replaces any top navigation bar with a fixed vertical sidebar on the left, applies consistent spacing and typography, and delivers a polished professional look matching tools like Linear, Notion, or Vercel's dashboard. Invoke when the user asks to redesign the UI, switch to a sidebar layout, modernize the look, or apply a SaaS style.
---

# SaaS UI Redesign

Transform the app's layout and visual design into a modern, professional SaaS interface. The result should feel like a mature product — clean, calm, and built for daily use.

## Phase 1: Explore

Before touching any file, read and understand the current structure. Use the Explore subagent for this phase.

Gather:
1. **`App.vue`** — full file. Identify: layout structure, nav link list (paths + labels), imported components, global CSS classes defined here (especially `top-nav`, `nav-tabs`, `main-content`, `card`, `badge`, `stat-card`, etc.)
2. **All view files** in `client/src/views/` — skim each for page structure patterns and any layout-specific classes
3. **All component files** in `client/src/components/` — identify which ones render in the nav area vs. content area (e.g., FilterBar, ProfileMenu, LanguageSwitcher)
4. **`main.js`** — extract the full route list (path → component name)
5. Note every CSS class that is used across multiple views and must remain compatible

Report back: route list, nav component names, global CSS class inventory, current layout structure.

## Phase 2: Design

Plan the new layout before writing code. The target structure:

```
┌──────────────────────────────────────────────────┐
│ ┌────────┐ ┌─────────────────────────────────── │
│ │        │ │  FilterBar (sticky inside content) │ │
│ │Sidebar │ ├────────────────────────────────────│ │
│ │        │ │                                    │ │
│ │  Nav   │ │   <router-view />                  │ │
│ │ Links  │ │                                    │ │
│ │        │ │                                    │ │
│ │        │ │                                    │ │
│ │ ────── │ │                                    │ │
│ │Profile │ │                                    │ │
│ └────────┘ └────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Sidebar anatomy (top to bottom)
1. **App identity** — logo mark + app name + optional subtitle, ~70px tall, matching the old nav height for visual continuity
2. **Nav links** — one per route, with an icon, a label, and an active state. Group into sections if there are 6+ links (e.g. "Overview", "Operations", "Analytics")
3. **Bottom section** — LanguageSwitcher (if present) + ProfileMenu trigger, pinned to bottom

### Icons
Use inline SVG for nav icons — no external icon library needed. Each icon should be ~18×18px, `stroke="currentColor"`, `stroke-width="1.75"`, `fill="none"`. Pick from these patterns or draw minimal equivalents:

- Dashboard/Overview: grid of 4 squares
- Inventory: box/cube outline
- Orders: clipboard or list with checkmark
- Finance/Spending: currency circle or chart bars
- Demand: trending arrow
- Reports: bar chart
- Restocking: refresh arrows around a box

If a route name is ambiguous, use a simple geometric icon (circle, square, triangle) rather than a wrong metaphor.

### Color tokens

```css
/* Sidebar */
--sidebar-bg: #ffffff;
--sidebar-border: #e2e8f0;
--sidebar-width: 240px;

/* Nav items */
--nav-text: #64748b;
--nav-text-hover: #0f172a;
--nav-text-active: #2563eb;
--nav-bg-hover: #f1f5f9;
--nav-bg-active: #eff6ff;
--nav-active-bar: #2563eb;   /* 3px left border on active link */

/* App background */
--content-bg: #f8fafc;

/* Typography */
--nav-font-size: 0.875rem;
--nav-font-weight: 500;

/* Spacing */
--nav-item-px: 12px;
--nav-item-py: 8px;
--nav-item-gap: 4px;         /* gap between icon and label */
--section-gap: 24px;         /* gap between nav groups */
```

## Phase 3: Implementation

**MANDATORY RULE**: Every `.vue` file change MUST be delegated to the `vue-expert` subagent. Do not edit `.vue` files directly.

### 3a. Delegate to vue-expert for App.vue

Give vue-expert a full, self-contained brief including:
- The complete current App.vue content (copy it in)
- The exact route list from Phase 1
- The component list (what to keep, what moves into sidebar)
- The full icon SVG strings for each nav link
- The CSS token values above
- These precise instructions:

**App.vue changes:**

1. **Remove** `.top-nav`, `.nav-container`, `.nav-tabs` and all their contents from the template and styles
2. **Add** a `.sidebar` element as the first child of `.app`, containing:
   - `.sidebar-header`: app identity (logo mark + name + subtitle if present)
   - `.sidebar-nav`: nav links as `<router-link>` elements, each with an icon `<svg>` and a `<span>` label; wrap in `.nav-group` sections if needed
   - `.sidebar-footer`: LanguageSwitcher + ProfileMenu trigger
3. **Rename** `.main-content` wrapper to keep the class but change its role — it now sits beside the sidebar, not below a top nav. Remove any `padding-top` offsets that compensated for the sticky header.
4. **Move** `<FilterBar />` inside the main content area (it was between header and router-view; now it goes just above `<router-view />` inside `.main-content`)
5. **Update layout CSS** on `.app`:
   ```css
   .app {
     display: flex;
     flex-direction: row;
     min-height: 100vh;
     background: var(--content-bg);
   }
   ```
6. **Add sidebar CSS** (scoped or global, matching existing pattern in the file):
   ```css
   .sidebar {
     width: var(--sidebar-width);
     min-width: var(--sidebar-width);
     background: var(--sidebar-bg);
     border-right: 1px solid var(--sidebar-border);
     display: flex;
     flex-direction: column;
     height: 100vh;
     position: sticky;
     top: 0;
     overflow-y: auto;
     z-index: 100;
   }
   .sidebar-header {
     padding: 20px 16px 16px;
     border-bottom: 1px solid var(--sidebar-border);
   }
   .sidebar-header h1 {
     font-size: 1rem;
     font-weight: 700;
     color: #0f172a;
     letter-spacing: -0.015em;
   }
   .sidebar-header .subtitle {
     font-size: 0.75rem;
     color: #94a3b8;
     font-weight: 400;
     border: none;
     padding: 0;
     margin-top: 2px;
     display: block;
   }
   .sidebar-nav {
     flex: 1;
     padding: 12px 8px;
     display: flex;
     flex-direction: column;
     gap: 2px;
   }
   .nav-group-label {
     font-size: 0.688rem;
     font-weight: 700;
     text-transform: uppercase;
     letter-spacing: 0.07em;
     color: #94a3b8;
     padding: 8px 8px 4px;
     margin-top: 8px;
   }
   .sidebar-nav a {
     display: flex;
     align-items: center;
     gap: 10px;
     padding: 8px 10px;
     border-radius: 6px;
     font-size: 0.875rem;
     font-weight: 500;
     color: #64748b;
     text-decoration: none;
     transition: background 0.15s ease, color 0.15s ease;
   }
   .sidebar-nav a:hover {
     background: #f1f5f9;
     color: #0f172a;
   }
   .sidebar-nav a.active {
     background: #eff6ff;
     color: #2563eb;
     position: relative;
   }
   .sidebar-nav a.active::before {
     content: '';
     position: absolute;
     left: 0;
     top: 4px;
     bottom: 4px;
     width: 3px;
     background: #2563eb;
     border-radius: 0 2px 2px 0;
   }
   .sidebar-nav svg {
     flex-shrink: 0;
     opacity: 0.75;
   }
   .sidebar-nav a.active svg,
   .sidebar-nav a:hover svg {
     opacity: 1;
   }
   .sidebar-footer {
     padding: 12px 8px;
     border-top: 1px solid #e2e8f0;
     display: flex;
     align-items: center;
     gap: 8px;
   }
   .main-content {
     flex: 1;
     min-width: 0;
     overflow-y: auto;
     display: flex;
     flex-direction: column;
   }
   ```
7. **Preserve** all existing global styles (`card`, `badge`, `stat-card`, `table`, etc.) — do not remove or rename them
8. **Add CSS custom properties** to `:root` or `*` at the top of the style section

### 3b. FilterBar positioning

If FilterBar has `position: sticky; top: 70px` (the old nav height), update it to `top: 0` inside the new layout where it sticks to the top of the scrolling content column.

Read `client/src/components/FilterBar.vue` and check for any sticky positioning. If found, delegate the fix to vue-expert.

### 3c. View-level spacing (optional pass)

After the layout changes land and the dev server confirms no errors, do a second pass:

Check the first view (Dashboard or equivalent). If the page header has excessive top margin or padding that assumed a sticky top nav above it, adjust to `margin-bottom: 1.5rem` with no forced top offset. Delegate any `.vue` changes to vue-expert.

## Phase 4: Verify

1. Start the dev server if not running: `cd client && npm run dev`
2. Check the browser at `http://localhost:3000`:
   - Sidebar appears on the left, all routes listed
   - Active route is highlighted with the blue left bar
   - Clicking a link navigates correctly and updates the active state
   - FilterBar renders below the sidebar header, above the page content
   - No horizontal scrollbar on the main content
   - Profile and language switcher are accessible in the sidebar footer
3. Check the browser console for Vue errors — fix any that appear before reporting done

## Guiding principles

- **Preserve all functionality** — no route, filter, modal, or data flow should break
- **Minimal surface area** — only change layout and visual styles; leave component logic untouched
- **No new dependencies** — inline SVG only, no icon packages
- **Keep global CSS classes intact** — `card`, `badge`, `stat-card`, and table styles are used by all views; rename nothing
- **One vue-expert call per .vue file** — batch all changes to a given file into a single delegation rather than multiple rounds
