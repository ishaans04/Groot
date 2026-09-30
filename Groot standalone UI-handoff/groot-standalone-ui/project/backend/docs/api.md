# GROOT service request guide

This guide shows how to talk to the local GROOT service. A service request sends a small JSON message to the program while it is running. The examples use `http://127.0.0.1:8000/api`.

## In everyday language

- A **task** is one question or choice GROOT is helping with. The service calls it a mission in saved records and request paths.
- A **fact** is something checked, missing, assumed, or not yet compared with other records.
- **Evidence** is a fact with the sample record it came from and the time it was checked.
- **History** is a saved choice and what happened later. A future task can use that history.
- A **Decision Room session** is a place to enter meeting statements after people have agreed to take part. This demo does not record audio.

## Open the sample company

| Request | What you will see |
| --- | --- |
| `GET /health` | Whether the service is running |
| `GET /dashboard` | Counts for tasks, sample suppliers, sales, and manufacturers |
| `GET /sources` | The sample business records GROOT can use |
| `GET /scenarios` | Suggested questions to try |
| `GET /decision-room/sample` | Four written meeting statements for the demo |
| `GET /missions` | Recent tasks saved by the service |
| `GET /missions/{id}` | One task, what it needs, and its result |
| `GET /missions/{id}/evidence` | The facts gathered and where they came from |
| `GET /memory` | Past choices, results, and lessons used later |

Task replies include a short status such as “Waiting for a key fact,” “Needs your answer,” “Ready for a person to choose,” or “Result recorded for future tasks.” The response also includes a shorter code such as `blocked` or `learned` for the service to use.

## Present the supplier choice from start to finish

Use `../demo.http` for ready-to-send examples. Replace `MISSION_ID` with the id returned by the first request.

1. Create the task by sending `POST /missions` with:

   `{"prompt":"Should we move 30% of production from Supplier A to B for Q4?","channel":"typed"}`

2. Send `POST /missions/{id}/execute`. GROOT shows the current price and the Q4 capacity question that must be answered before a person can save a choice.

3. Fill in these five missing facts one by one with `POST /missions/{id}/acquire`:

   - `{"variable_id":"peak_capacity"}`
   - `{"variable_id":"lead_time"}`
   - `{"variable_id":"defect_rate"}`
   - `{"variable_id":"minimum_order"}`
   - `{"variable_id":"transition_cost"}`

   Each reply says which sample record supplied the information, when that record was updated, and how certain the match is. Price is already present, so the task has six facts in total. The sample math shows 12,000 spare units at Supplier B versus 14,100 units in a 30% shift, a possible 2,100-unit shortfall. That calculation uses sample commitments and is marked as an estimate. A person still decides what to do.

4. After all six facts are checked, save a human choice with `POST /missions/{id}/decision` and:

   `{"choice":"Shift allocation to Supplier B","rationale":"The decision owner reviewed the sample records."}`

   GROOT will not save a choice while a required fact is missing.

5. Record the later result with `POST /missions/{id}/outcome` and:

   `{"observed":"Supplier B met Q4 volume; lead time ran four days longer than planned."}`

6. Open `GET /memory`, then create the same supplier task again. The earlier result makes Q4 capacity an important check in the new task.

## Try the other examples

- **Direct answer:** Ask “What were Q2 sales in Maharashtra?” and run the task. GROOT adds two matching sample rows and shows the records underneath. If a question leaves out the region or time period, it asks what to use instead of guessing.
- **Sales investigation:** Ask “Why did sales decline in the North in Q2 2026?” and run the task. The sample records show a 14.1% decrease and the change for each sales channel. Other possible explanations stay marked as unconfirmed; these records cannot prove why sales fell.
- **Manufacturer search:** Ask “Find 8 manufacturers in India with ISO 9001 and monthly capacity above 15000 units.” and run the task. GROOT returns up to eight matching sample records.

## Enter a meeting statement

Start with `POST /decision-room/sessions` and a clear purpose:

`{"consent":true,"purpose":"Supplier allocation review: Q4 capacity and allocation"}`

The service requires `consent` to be exactly `true`. If it is missing or false, the session does not start. This is a demo consent record; get agreement before entering any real discussion.

Enter a written statement with `POST /decision-room/sessions/{session_id}/events`:

`{"speaker":"COO","text":"We don't have a recent capacity confirmation."}`

GROOT marks capacity as missing on the same supplier task. It keeps the quote as something a person said; it does not treat the quote as proof. Or load the four written example statements with `POST /decision-room/sessions/{session_id}/replay-sample`. Close the session with `POST /decision-room/sessions/{session_id}/close`. A closed session will not accept more statements.

The four prepared meeting statements are listed at `GET /decision-room/sample`. The service adds them only after a consented session has started.

## Replies and sample-data note

Successful requests return JSON. A new task returns `201`; a completed action returns `200`. Invalid input returns `400`, a missing task returns `404`, a room without consent returns `403`, and an attempt to update a closed room returns `409`. Each error includes a plain-language `message`.

All company, sales, supplier, and manufacturer records are fictional. The service does not connect to a real company, check live outside records, record a microphone, or choose a supplier. Use it as a presentation prototype only.
