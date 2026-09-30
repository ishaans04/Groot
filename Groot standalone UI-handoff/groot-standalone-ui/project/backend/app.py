"""Run the local GROOT API and serve the unchanged handoff UI from one origin."""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

BACKEND = Path(__file__).resolve().parent
PROJECT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from groot import seed  # noqa: E402
from groot.compiler import compile_prompt  # noqa: E402
from groot.engine import acquire, execute, record_outcome, record_room_statement, save_decision  # noqa: E402
from groot.store import Store  # noqa: E402

DB_PATH = Path(os.environ.get("GROOT_DB", str(BACKEND / "runtime" / "groot-demo.sqlite3")))
STORE = Store(DB_PATH)
STORE.seed_demo()


class Handler(SimpleHTTPRequestHandler):
    server_version = "GROOTPrototype/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, status: int, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        if size > 64_000:
            raise ValueError("Request body exceeds 64 KB.")
        raw = self.rfile.read(size) if size else b"{}"
        try:
            obj = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid JSON.") from exc
        if not isinstance(obj, dict):
            raise ValueError("Request body must be a JSON object.")
        return obj

    def list_directory(self, path):
        # Never expose folder contents; the project has no index.html files.
        self.send_error(404, "Not found")
        return None

    def redirect_root(self) -> bool:
        if unquote(urlparse(self.path).path) != "/":
            return False
        self.send_response(302)
        self.send_header("Location", "/GROOT.dc.html")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return True

    def do_HEAD(self):
        if not self.redirect_root():
            super().do_HEAD()

    def do_GET(self):
        if self.redirect_root():
            return None
        path = unquote(urlparse(self.path).path)
        if not path.startswith("/api/"):
            return super().do_GET()
        try:
            if path == "/api/health":
                return self.send_json(200, {"service": "GROOT Prototype API", "status": "ok", "version": "0.1.0", "storage": "sqlite", "mode": "offline seeded fixtures"})
            if path == "/api/sources":
                return self.send_json(200, {"sources": seed.SOURCES})
            if path == "/api/scenarios":
                return self.send_json(200, {"scenarios": seed.DEMO_SCENARIOS})
            if path == "/api/decision-room/sample":
                return self.send_json(200, {"statements": seed.ROOM_SEGMENTS, "note": "These are written sample statements. This service does not record audio."})
            if path == "/api/dashboard":
                missions = STORE.missions(100)
                memory = STORE.memory()
                states = {state: sum(m["status"] == state for m in missions) for state in ("blocked", "open", "awaiting_input", "ready", "saved", "learned", "complete")}
                return self.send_json(200, {"organization": seed.ORGANIZATION["name"], "as_of": seed.ORGANIZATION["as_of"], "mission_count": len(missions), "mission_states": states, "supplier_count": len(seed.SUPPLIERS), "sales_records": len(seed.SALES), "manufacturer_records": len(seed.MANUFACTURERS), "room_demo_statements": len(seed.ROOM_SEGMENTS), "presentation_scenarios": len(seed.DEMO_SCENARIOS), "memory_rule_count": len(memory["rules"]), "sources": {"permitted": sum(s["permitted"] for s in seed.SOURCES), "total": len(seed.SOURCES)}})
            if path == "/api/memory":
                return self.send_json(200, STORE.memory())
            if path == "/api/missions":
                return self.send_json(200, {"missions": STORE.missions()})
            match = re.fullmatch(r"/api/missions/([^/]+)(?:/(evidence))?", path)
            if match:
                mission_id = match.group(1)
                mission = STORE.get_mission(mission_id)
                if not mission:
                    return self.send_json(404, {"error": "mission_not_found", "message": f"No mission {mission_id}."})
                if match.group(2):
                    return self.send_json(200, {"evidence": STORE.evidence_for(mission_id)})
                return self.send_json(200, {"mission": mission})
            return self.send_json(404, {"error": "not_found", "message": "Unknown API route."})
        except Exception as exc:
            return self.send_json(500, {"error": "server_error", "message": str(exc)})

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        try:
            body = self.body()
            if path == "/api/missions":
                mission = compile_prompt(str(body.get("prompt", "")), str(body.get("channel", "typed")), STORE.memory()["rules"])
                STORE.log(mission["id"], "mission.compiled", {"channel": mission["channel"], "type": mission["type"]})
                STORE.save_mission(mission)
                return self.send_json(201, {"mission": mission})
            match = re.fullmatch(r"/api/missions/([^/]+)/(execute|acquire|decision|outcome)", path)
            if match:
                mission_id, action = match.groups()
                mission = STORE.get_mission(mission_id)
                if not mission:
                    return self.send_json(404, {"error": "mission_not_found", "message": f"No mission {mission_id}."})
                if action == "execute":
                    return self.send_json(200, {"mission": execute(STORE, mission)})
                if action == "acquire":
                    return self.send_json(200, acquire(STORE, mission, str(body.get("variable_id", ""))))
                if action == "decision":
                    updated = save_decision(STORE, mission, str(body.get("choice", "")), str(body.get("rationale", "")))
                    return self.send_json(200, {"mission": updated})
                result = record_outcome(STORE, mission, str(body.get("observed", "")))
                return self.send_json(201, result)
            if path == "/api/decision-room/sessions":
                if body.get("consent") is not True:
                    return self.send_json(403, {"error": "consent_required", "message": "Decision Room capture starts only after explicit participant consent."})
                purpose = str(body.get("purpose", "" )).strip()
                if not purpose:
                    return self.send_json(400, {"error": "purpose_required", "message": "State the purpose of this consented demo session."})
                mission_id = body.get("mission_id")
                mission = STORE.get_mission(str(mission_id)) if mission_id else None
                if mission_id and not mission:
                    return self.send_json(404, {"error": "mission_not_found", "message": f"No mission {mission_id}."})
                if mission and mission["type"] not in {"decision", "ambient"}:
                    return self.send_json(400, {"error": "decision_mission_required", "message": "Decision Room signals must attach to a decision mission."})
                if mission and mission["status"] not in {"blocked", "open", "ready"}:
                    return self.send_json(409, {"error": "decision_closed", "message": "Decision Room signals cannot update a saved or completed decision."})
                if mission is None:
                    mission = compile_prompt(purpose, "decision_room", STORE.memory()["rules"])
                    STORE.save_mission(mission)
                session_id = "ROOM-" + uuid.uuid4().hex[:8].upper()
                STORE.start_room(session_id, mission["id"], True, purpose)
                STORE.log(mission["id"], "decision_room.consent_granted", {"session_id": session_id, "purpose": purpose})
                return self.send_json(201, {"session": {"id": session_id, "consent": True, "purpose": purpose}, "mission": mission, "message": "Consent recorded. Demo signal processing is active."})
            match = re.fullmatch(r"/api/decision-room/sessions/([^/]+)/(events|close|replay-sample)", path)
            if match:
                session_id, action = match.groups()
                session = STORE.room_session(session_id)
                if not session or not session["consent"]:
                    return self.send_json(403, {"error": "consent_required", "message": "No active consented session exists."})
                if session["ended_at"]:
                    return self.send_json(409, {"error": "session_closed", "message": "This Decision Room session is closed."})
                if action == "close":
                    STORE.db.execute("UPDATE room_sessions SET ended_at=? WHERE id=?", (now_iso(), session_id))
                    STORE.db.commit()
                    STORE.log(None, "decision_room.closed", {"session_id": session_id})
                    return self.send_json(200, {"session_id": session_id, "consent": True, "status": "closed"})
                mission_id = session["mission_id"]
                mission = STORE.get_mission(mission_id)
                if action == "replay-sample":
                    results = [record_room_statement(STORE, mission, session_id, segment["speaker"], segment["text"], segment) for segment in seed.ROOM_SEGMENTS]
                    return self.send_json(200, {"events": [result["event"] for result in results], "mission": results[-1]["mission"], "note": "Four written statements were added to the consented session. No audio was recorded."})
                text = str(body.get("text", "")).strip()
                speaker = str(body.get("speaker", "Participant")).strip()[:80]
                if not text or len(text) > 1000:
                    return self.send_json(400, {"error": "invalid_segment", "message": "Event text must contain 1 to 1,000 characters."})
                return self.send_json(201, record_room_statement(STORE, mission, session_id, speaker, text))
            return self.send_json(404, {"error": "not_found", "message": "Unknown API route."})
        except KeyError as exc:
            return self.send_json(404, {"error": "not_found", "message": str(exc).strip("'")})
        except ValueError as exc:
            return self.send_json(400, {"error": "invalid_request", "message": str(exc)})
        except Exception as exc:
            return self.send_json(500, {"error": "server_error", "message": str(exc)})


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main():
    # Render provides PORT at runtime. Keep GROOT_PORT as the convenient local
    # override, while still allowing PORT to take precedence on the hosted app.
    host = os.environ.get("GROOT_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("GROOT_PORT", "8000")))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"GROOT prototype ready at http://{host}:{port}/")
    print(f"API request guide: http://{host}:{port}/backend/docs/api.md")
    print(f"Console UI: http://{host}:{port}/GROOT.dc.html")
    print(f"SQLite store: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping GROOT prototype.")
    finally:
        server.server_close()
        STORE.close()


if __name__ == "__main__":
    main()
