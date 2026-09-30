"""Small SQLite repository; each prototype entity remains inspectable JSON."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from . import seed
from .compiler import STATE_LABELS, STATUS_LABELS, now


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS missions(id TEXT PRIMARY KEY, topic TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL, variable_id TEXT NOT NULL, source_id TEXT NOT NULL, claim TEXT NOT NULL, value TEXT NOT NULL, confidence REAL NOT NULL, observed_at TEXT NOT NULL, lineage TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outcomes(id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL, topic TEXT NOT NULL, decision TEXT NOT NULL, observed TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS memory_rules(id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL, rule TEXT NOT NULL, support_count INTEGER NOT NULL, updated_at TEXT NOT NULL, UNIQUE(topic, rule));
        CREATE TABLE IF NOT EXISTS room_sessions(id TEXT PRIMARY KEY, mission_id TEXT NOT NULL, consent INTEGER NOT NULL, purpose TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT);
        CREATE TABLE IF NOT EXISTS room_events(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, mission_id TEXT, speaker TEXT NOT NULL, text TEXT NOT NULL, signal TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT, action TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
        """)
        self.db.commit()

    def seed_demo(self) -> None:
        existing = self.db.execute("SELECT 1 FROM missions LIMIT 1").fetchone()
        if existing:
            return
        history = seed.HISTORY
        self.save_mission(history["mission"])
        outcome = history["outcome"]
        self.db.execute("INSERT INTO outcomes(mission_id,topic,decision,observed,created_at) VALUES(?,?,?,?,?)", (outcome["mission_id"], outcome["topic"], outcome["decision"], outcome["observed"], outcome["created_at"]))
        rule = history["memory_rule"]
        self.db.execute("INSERT INTO memory_rules(topic,rule,support_count,updated_at) VALUES(?,?,?,?)", (rule["topic"], rule["rule"], rule["support_count"], rule["updated_at"]))
        self.db.commit()

    def save_mission(self, mission: dict) -> dict:
        stamp = now()
        mission["updated_at"] = stamp
        mission["status_label"] = STATUS_LABELS.get(mission["status"], mission["status"])
        for variable in mission.get("variables", []):
            variable["state_label"] = STATE_LABELS.get(variable["state"], variable["state"])
            variable["blocks_choice"] = bool(variable.get("critical"))
        if mission.get("decision"):
            labels = {"blocked": "Waiting for a key fact", "ready": "Ready for a person to choose", "saved": "Choice saved"}
            mission["decision"].setdefault("state_label", labels.get(mission["decision"].get("state"), "Recorded choice"))
        self.db.execute("INSERT INTO missions(id,topic,kind,status,created_at,updated_at,payload) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET topic=excluded.topic,kind=excluded.kind,status=excluded.status,updated_at=excluded.updated_at,payload=excluded.payload",
                        (mission["id"], mission.get("topic", "general"), mission["type"], mission["status"], mission.get("created_at", stamp), stamp, json.dumps(mission, ensure_ascii=False)))
        self.db.commit()
        return mission

    def get_mission(self, mission_id: str) -> dict | None:
        row = self.db.execute("SELECT payload FROM missions WHERE id=?", (mission_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def missions(self, limit: int = 50) -> list[dict]:
        rows = self.db.execute("SELECT payload FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def log(self, mission_id: str | None, action: str, detail: Any, actor: str = "demo-user") -> None:
        self.db.execute("INSERT INTO audit_log(mission_id,action,actor,detail,created_at) VALUES(?,?,?,?,?)", (mission_id, action, actor, json.dumps(detail, ensure_ascii=False), now()))
        self.db.commit()

    def add_evidence(self, mission_id: str, variable_id: str, source_id: str, claim: str, value: Any, confidence: float, lineage: dict) -> dict:
        stamp = now()
        row_id = self.db.execute("INSERT INTO evidence(mission_id,variable_id,source_id,claim,value,confidence,observed_at,lineage) VALUES(?,?,?,?,?,?,?,?)",
                                 (mission_id, variable_id, source_id, claim, json.dumps(value, ensure_ascii=False), confidence, stamp, json.dumps(lineage, ensure_ascii=False))).lastrowid
        self.db.commit()
        return {"id": row_id, "mission_id": mission_id, "variable_id": variable_id, "source_id": source_id, "claim": claim, "value": value, "confidence": confidence, "observed_at": stamp, "lineage": lineage}

    def evidence_for(self, mission_id: str) -> list[dict]:
        rows = self.db.execute("SELECT * FROM evidence WHERE mission_id=? ORDER BY id", (mission_id,)).fetchall()
        return [{**dict(r), "value": json.loads(r["value"]), "lineage": json.loads(r["lineage"])} for r in rows]

    def record_outcome(self, mission_id: str, topic: str, decision: str, observed: str) -> dict:
        stamp = now()
        self.db.execute("INSERT INTO outcomes(mission_id,topic,decision,observed,created_at) VALUES(?,?,?,?,?)", (mission_id, topic, decision, observed, stamp))
        rule = "Peak capacity must be confirmed before recommending an allocation shift." if topic == "supplier" and "capacity" in observed.casefold() else "Record this outcome as context for similar future missions."
        self.db.execute("INSERT INTO memory_rules(topic,rule,support_count,updated_at) VALUES(?,?,1,?) ON CONFLICT(topic,rule) DO UPDATE SET support_count=support_count+1,updated_at=excluded.updated_at", (topic, rule, stamp))
        self.db.commit()
        return {"mission_id": mission_id, "topic": topic, "decision": decision, "observed": observed, "created_at": stamp, "learning_delta": rule}

    def memory(self) -> dict:
        rules = [dict(r) for r in self.db.execute("SELECT topic,rule,support_count,updated_at FROM memory_rules ORDER BY updated_at DESC")]
        outcomes = [dict(r) for r in self.db.execute("SELECT mission_id,topic,decision,observed,created_at FROM outcomes ORDER BY created_at DESC LIMIT 20")]
        return {"rules": rules, "outcomes": outcomes, "principle": "Past choices and later results guide similar future tasks. The demo does not train an AI model."}

    def start_room(self, session_id: str, mission_id: str, consent: bool, purpose: str) -> None:
        self.db.execute("INSERT INTO room_sessions(id,mission_id,consent,purpose,started_at) VALUES(?,?,?,?,?)", (session_id, mission_id, int(consent), purpose, now()))
        self.db.commit()

    def room_session(self, session_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM room_sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None

    def room_event(self, session_id: str, mission_id: str, speaker: str, text: str, signal: str) -> dict:
        stamp = now()
        event_id = self.db.execute("INSERT INTO room_events(session_id,mission_id,speaker,text,signal,created_at) VALUES(?,?,?,?,?,?)", (session_id, mission_id, speaker, text, signal, stamp)).lastrowid
        self.db.commit()
        return {"id": event_id, "session_id": session_id, "mission_id": mission_id, "speaker": speaker, "text": text, "signal": signal, "created_at": stamp}

    def close(self) -> None:
        self.db.close()
