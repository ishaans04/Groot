# GROOT — Presentation Prototype

The folder contains GROOT's website and a small local service for the presentation. The website introduces the product and shows its example console. The service runs sample questions, supplier choices, meeting statements, and saved results.

The presentation includes the existing website and a separate offline service with sample company records. It can turn a request into a task, find sample information, show what is still unknown, save a choice, and record what happened later. The website files are unchanged, so the website demo and the service demo still run separately.

The repository also includes a root-level [`render.yaml`](render.yaml) for deploying the website and API together as one Render web service. Read the [Render deployment guide](Groot%20standalone%20UI-handoff/groot-standalone-ui/project/backend/docs/render-deployment.md) before creating the paid service and its persistent disk.

## Project layout

```
Groot standalone UI-handoff/groot-standalone-ui/project/
├── GROOT Standalone.html   # One-file version of the website
├── GROOT.dc.html           # Main design: landing page + console
├── GROOT v2.dc.html        # Earlier iteration
├── GROOT v1.dc.html        # Earlier "Mission Control" iteration
├── support.js              # Adds behavior to the main website pages
├── assets/
│   ├── groot-styles.css    # Shared styles
│   └── icons.js            # Icon set
├── backend/                # Offline service, saved demo state and sample data
│   ├── app.py
│   ├── groot/              # Request handling, decision rules and saved records
│   ├── data/               # Editable sample company records and demo history
│   ├── README.md
│   ├── docs/               # Plain-language service and presentation guides
│   └── demo.http
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

The service needs Python 3.10 or newer and uses only Python's built-in tools. From the project folder, run:

```powershell
cd backend
start-prototype.cmd
```

Then open <http://127.0.0.1:8000/GROOT.dc.html>. The service also starts at <http://127.0.0.1:8000/api/health>. See `backend/README.md` for setup and `backend/demo.http` for the sample presentation steps. All saved demo activity goes to `backend/runtime/groot-demo.sqlite3`.
