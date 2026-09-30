# Demo data

Everything in this folder is made up for the GROOT presentation. The service reads these files when it starts; it does not contact the businesses or outside services named here.

- `organization.json` describes the sample company and what this demo can do.
- `sources.json` lists the sample files and systems that the demo pretends are connected.
- `suppliers.json` contains three sample suppliers and their costs, capacity, quality, and delivery figures.
- `sales.json` contains seven sample quarterly sales rows.
- `manufacturers.json` contains twelve sample manufacturers for the supplier search.
- `decision_room.json` contains four written meeting statements for the room demonstration.
- `scenarios.json` contains five prompts you can show during a presentation.
- `history.json` starts the demo with one earlier supplier choice, its result, and the lesson carried forward.

Keep these files as the single source for demo data. Edit the JSON, then restart `app.py` to load changes. Existing saved work in the SQLite file stays as it is.
