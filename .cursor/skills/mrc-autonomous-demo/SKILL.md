---
name: mrc-autonomous-demo
description: >-
  Adds or updates an autonomous (self-driving) timed demo walkthrough on MRC
  networking HTML visualizations — scene script, progress bar, captions, and
  refactored fault controls. Use when the user asks for an autonomous demo,
  self-driving demo, demo walkthrough, or recallable demo for MRC/multipath/
  multiplane HTML pages, or when extending docs/assets/mrc_multipath_multiplane.html
  or similar content/html/*.html simulations.
---

# MRC Autonomous Demo

Add a **Run demo** mode to standalone MRC HTML canvas pages. The demo resets state, drives fault buttons on a timed script, shows scene captions, and disables manual fault controls while running.

## When to apply

- User wants an autonomous / self-driving / scripted demo on an MRC HTML page
- User says "recall this" or "make it a skill" for the MRC demo pattern
- Adding demo mode to a new `content/html/*.html` or `docs/assets/*.html` visualization

## Canonical reference

The full working implementation lives in:

- `docs/assets/mrc_multipath_multiplane.html` — reference page with demo already integrated
- [reference.md](reference.md) — copy-paste blocks (CSS, HTML, JS scaffold, scene template)

Read the reference file before editing; match its naming and structure.

## Workflow

```
Task Progress:
- [ ] Read target HTML and identify existing controls (congest, break, fail plane, trim, reset, rate)
- [ ] Refactor inline onclick handlers into named setters (setCongest, setBroken, …)
- [ ] Add demo UI (Run demo button, progress bar, caption panel)
- [ ] Add DEMO_SCENES array and demo state machine (startDemo / stopDemo / demoTick)
- [ ] Wire demoTick into requestAnimationFrame step() using timestamp delta
- [ ] Verify manually in browser; sync to content/html/ if the page should appear in MkDocs
```

## Implementation rules

### 1. Refactor controls first

Extract fault toggles into functions the demo script can call. Each setter must update sim state **and** button labels:

```javascript
function setCongest(on) { /* evs[6], button label, bgd() */ }
function setBroken(on)  { /* evs[9], button label, bgd() */ }
function setPlaneFail(on) { /* planes[3], button label, bgd() */ }
function setTrim(on)    { /* trimOn, button label */ }
function clearAllFaults() { setCongest(false); setBroken(false); setPlaneFail(false); setTrim(true); }
```

Keep manual buttons; wire them to the setters.

### 2. Demo UI elements

Add before `#ctl`:

- `#demo-bar` / `#demo-prog` — thin progress bar per scene
- `#demo-cap` — scene title + caption + optional `<em>` hint
- `#b-demo` — **Run demo** / **Stop demo** (first control in `#ctl`)

Style `#b-demo.demo-on` with accent `#7F77DD`. Disable manual fault buttons while `demoOn`.

### 3. Scene script

Define `DEMO_SCRIPT` as `{ pause, btn, title, cap, em? }`:

- `pause` — seconds to observe **after** the button fires (progress bar fills during this)
- `btn` — fault button id to `.click()` (`b-cong`, `b-break`, `b-fail`, `b-trim`), or `null` for observe-only
- Each fault button is clicked for real via `fireBtn()` — labels and state stay in sync

Default sequence: baseline pause → congest → clear → break → repair → fail plane → restore → trim off → trim on.

### 4. Timing

- Track `lastTs` from `requestAnimationFrame(step)`.
- Call `demoTick(Math.min(0.1, (ts - lastTs) / 1000))` when `demoOn`.
- `startDemo()`: reset sim, unpause, save rate, show scene 0.
- `stopDemo()`: hide demo UI, restore rate, re-enable buttons.
- In `hud()`, skip live fault messages while `demoOn` (captions own the narrative).

### 5. MRC semantics (captions must distinguish)

- **Congestion** → CE marks, amber SACK, NSCC window cut; path **stays** in EV set
- **Broken path** → loss/trim, purple gap SACK, selective retransmit, eventual **denylist**
- **Plane port down** → Port Status excludes **all EVs on that plane** instantly
- **Trim off** → silent drops until gap SACK (slower detection)

Do not conflate congestion with failure in scene copy.

## MkDocs integration

If the page should appear on the docs site:

1. Copy (or symlink) the HTML to `content/html/<slug>.html`
2. Run `make generate` — updates `docs/generated/` and `mkdocs.yml` nav
3. Run `make build` — strict mode must pass

Standalone assets under `docs/assets/` are **not** auto-published; prefer `content/html/` for site pages.

## Customization

When the user requests changes:

- **Add/remove scenes** — edit `DEMO_SCENES`; keep total under ~60s unless asked otherwise
- **Different faults** — map `run()` to the page's existing buttons/state
- **Auto-start** — append `startDemo()` after init only if explicitly requested
- **Loop** — in `demoTick`, reset `demoScene = 0` instead of `stopDemo()` at end

## Verification

1. Open the HTML file in a browser (or `make serve` if in `content/html/`)
2. Click **Run demo** — scenes advance, progress bar fills, captions update
3. **Stop demo** mid-run — manual controls re-enable
4. **Reset** during demo — stops demo and clears state
