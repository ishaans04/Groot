# GROOT — Standalone Frontend

Static HTML/CSS/JS frontend for **GROOT: Organizational Intelligence Through Natural Language**. It contains the landing page (Product, Architecture, Decision Room and Roadmap sections) and the GROOT Console (mission compiler log, decision graph, decision state and memory).

This is a frontend-only prototype: there is no backend and no build step.

## Project layout

```
Groot standalone UI-handoff/groot-standalone-ui/project/
├── GROOT Standalone.html   # Single-file bundle, everything inlined (easiest to open)
├── GROOT.dc.html           # Main design: landing page + console
├── GROOT v2.dc.html        # Earlier iteration
├── GROOT v1.dc.html        # Earlier "Mission Control" iteration
├── support.js              # Runtime that renders the .dc.html pages
├── assets/
│   ├── groot-styles.css    # Shared styles
│   └── icons.js            # Icon set
└── uploads/                # Reference material (concept paper PDF, screenshots)
```

## Previewing locally

### Option 1: open the standalone file

Double-click `GROOT Standalone.html`, or open it in any modern browser. It is self-contained and works straight from disk.

### Option 2: run a local server (recommended for the `.dc.html` pages)

The `.dc.html` pages load `support.js` and the files in `assets/`, and are best served over HTTP. From the `project` folder, run one of:

```bash
# Python 3
python -m http.server 8000

# Node.js
npx serve .
```

Then open <http://localhost:8000/GROOT.dc.html> (with `npx serve`, use the port it prints).

VS Code users can also right-click `GROOT.dc.html` and choose **Open with Live Server**.

### Requirements

- A modern browser (Chrome, Edge, Firefox or Safari).
- An internet connection: the pages load Google Fonts, and the `.dc.html` pages load React 18 and Babel from `unpkg.com` at runtime.
