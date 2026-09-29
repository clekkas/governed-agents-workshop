# Decks

Generators for the workshop PowerPoint decks.

- `build-addendum-deck.js` → `../foundry-phase2-build-addendum.pptx` — **as-built** supporting
  slides, one per shipped work item. Extend the slide blocks as we build (see
  `../build-log.md`), then regenerate.

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
