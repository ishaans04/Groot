# GROOT demo service

This local service gives the presentation working examples behind the website: typed requests, saved sample records, a supplier decision, consented meeting statements, and a recorded result that can guide a later decision.

## Start the presentation

From the project folder, open PowerShell and run:

```powershell
cd backend
.\start-prototype.cmd
```

Then use these pages:

- Website: <http://127.0.0.1:8000/GROOT.dc.html>
- Service status: <http://127.0.0.1:8000/api/health>
- Sample company overview: <http://127.0.0.1:8000/api/dashboard>
- Request guide: <http://127.0.0.1:8000/backend/docs/api.md>
- Plain-language speaking notes: <http://127.0.0.1:8000/backend/docs/presentation.md>

Keep the PowerShell window open while presenting. Stop the service with **Ctrl+C**. It runs on your computer only. If port 8000 is busy, set `$env:GROOT_PORT='8001'` before running the same command, then use port 8001 in the links.

## Deploy one full service to Render

The repository includes a root-level `render.yaml`. It creates one web service for both the website and API, plus a 1 GB persistent disk for saved demo activity. The disk requires a paid web-service plan. Follow the plain-language [Render deployment guide](docs/render-deployment.md) before creating the service.

## What the sample company contains

The sample records are made up and live in [`data/`](data/README.md): three suppliers, seven sales rows, twelve manufacturers, six named information sources, five example requests, four written meeting statements, and one earlier supplier decision with a recorded result. On first start, the service copies the earlier decision and its lesson into `runtime/groot-demo.sqlite3`. New choices and results are saved there, so they remain after restart.

Edit a JSON file in `data/` to change a sample record, then restart the service. Existing saved choices remain as they are. To begin with a fresh database, stop the service and point `GROOT_DB` to a new file path before starting it again.

## Recommended presentation order

1. Start with the supplier question in [`demo.http`](demo.http).
2. Show the sample price information and the missing Q4 capacity fact.
3. Fill in the missing supplier facts. Show that each one has a named source and a time when it was checked.
4. Save a human choice, then enter the later result.
5. Ask the same supplier question again. Show how the earlier result makes capacity a required check.
6. Use the other prompts in `demo.http` to show the sales answer, sales comparison, manufacturer list, and consented meeting statement.

The website and this service are separate demonstrations. The website files are unchanged; its buttons still use their original in-browser sample behavior. Use the request examples in `demo.http` to show the service behavior.

## What this prototype does and does not do

The service runs without internet access or extra software libraries. Its rules are written in Python, and its sample company records are JSON. It does not use an AI model, speak into a microphone, contact live company systems, search the live internet, or make a supplier choice for a person. Meeting statements require an explicit consent record and remain unconfirmed until checked against a named source.

Use [docs/presentation.md](docs/presentation.md) for a short script you can read while showing the examples. Use [docs/api.md](docs/api.md) for the exact requests and [demo.http](demo.http) for copy-ready examples.
