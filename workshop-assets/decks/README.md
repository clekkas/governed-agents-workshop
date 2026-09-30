# Decks

Generators for the workshop PowerPoint decks.

- `build-addendum-deck.js` → `../foundry-phase2-build-addendum.pptx` — **as-built** supporting
  slides, one per shipped work item. Extend the slide blocks as we build (see
  `../build-log.md`), then regenerate.
- `customer-priorities-deck.js` → `../kaiser-customer-priorities-briefs.pptx` — one slide per
  customer priority from the 9/29 KP planning call (agenda reorder, capability-host reuse + cost,
  secure MCP, existing-vs-Foundry Search, agent-type decision, healthcare content safety,
  CMK/AMPLS, SharePoint RAG, attendee→brief map). Each slide maps to a `docs/*.md` brief.
- `kaiser-consolidated-customer-deck.js` → `../kaiser-consolidated-customer-deck.pptx` — the
  **single consolidated customer presentation** (25 slides): title → agenda → why governed agents →
  scenario + safety boundary → reference architecture → the priority briefs (re-sequenced to
  the 9/29 order, including dedicated **Work IQ**, **"where the MCP server runs"**, and **RAG domain**
  slides) → end-to-end → evaluation gate → 30/60/90 roadmap → deeper-reading index → close.

## Delivering the deck

`../facilitator-delivery-plan.md` is the slide-keyed run script for the consolidated deck: for each
time block it maps which slides to show, the first-person talk track, and exactly when to break for a
demo (with copy-paste commands and checkpoint tags).

## Regenerate

Requires Node and `pptxgenjs`.

```powershell
cd workshop-assets\decks
npm install            # first time only (installs pptxgenjs)
node build-addendum-deck.js
```

If `pptxgenjs` is already installed elsewhere, point Node at it instead of installing:

```powershell
$env:NODE_PATH = "<path-to>\node_modules"; node build-addendum-deck.js
```

## Convention

One slide per shipped capability, reusing the main deck's theme/helpers (`slide`, `card`, `pill`,
`bullets`, `mono`, `notes`). Keep speaker notes on every slide. Keep text ASCII-safe (no curly
quotes / em dashes) so the file validates cleanly.
