"""Rule-based mission compiler with inspectable, deterministic output."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

STATUS_LABELS = {
    "blocked": "Waiting for a key fact",
    "open": "Needs more information",
    "awaiting_input": "Needs your answer",
    "ready": "Ready for a person to choose",
    "saved": "Choice saved",
    "learned": "Result recorded for future tasks",
    "complete": "Finished",
}
STATE_LABELS = {
    "known": "Checked",
    "unknown": "Not checked yet",
    "assumed": "Assumed for now",
    "conflicting": "Records disagree",
    "acquiring": "Checking now",
    "spec": "From your request",
    "option": "Choice",
    "dataset": "Not gathered yet",
}
TYPE_LABELS = {
    "direct": "Answer a question",
    "investigation": "Look into a change",
    "decision": "Help with a choice",
    "ambient": "Meeting discussion",
    "data": "Build a list",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def compile_prompt(prompt: str, channel: str = "typed", memory: list[dict] | None = None) -> dict:
    text = " ".join(prompt.strip().split())
    if not text:
        raise ValueError("A non-empty prompt is required.")
    if len(text) > 1600:
        raise ValueError("Prompt must be 1,600 characters or fewer.")
    if channel not in {"typed", "decision_room"}:
        raise ValueError("channel must be 'typed' or 'decision_room'.")

    lower = text.casefold()
    is_supplier = any(word in lower for word in ("supplier", "vendor", "production allocation"))
    if channel == "decision_room" or any(term in lower for term in ("concern is whether", "worried about", "can they handle", "don't have recent", "do not have recent")):
        kind = "ambient" if channel == "decision_room" else "decision"
    elif any(term in lower for term in ("should we", "should i", "decide", "switch", "move ", "choose between", "which option")):
        kind = "decision"
    elif any(term in lower for term in ("why ", "why did", "explain", "investigate", "what caused")):
        kind = "investigation"
    elif any(term in lower for term in ("find ", "list ", "collect ", "manufacturers matching", "build a dataset")):
        kind = "data"
    else:
        kind = "direct"

    quantity = re.search(r"\b(\d{1,4})\s*(?:%|percent|manufacturers?|suppliers?|records?|companies|items)?\b", lower)
    quarter = re.search(r"\bq([1-4])(?:\s+(20\d{2}))?\b", lower)
    percent = re.search(r"\b(\d{1,3})\s*(?:%|percent)\b", lower)
    constraints = []
    if percent:
        constraints.append({"type": "allocation_percent", "value": int(percent.group(1)), "raw": percent.group(0)})
    if quantity and kind == "data":
        constraints.append({"type": "limit", "value": int(quantity.group(1)), "raw": quantity.group(0)})
    if "iso 9001" in lower:
        constraints.append({"type": "certification", "value": "ISO 9001"})
    capacity = re.search(r"(?:above|over|at least|minimum(?: of)?)\s+(\d[\d,]*)\s*(?:units?)?", lower)
    if capacity and kind == "data":
        constraints.append({"type": "min_monthly_capacity", "value": int(capacity.group(1).replace(",", ""))})
    geography = next((name for name in ("Maharashtra", "North", "India", "Pune", "Tamil Nadu") if name.casefold() in lower), None)

    variables: list[dict] = []
    options: list[dict] = []
    topic = "supplier" if is_supplier else ("sales" if "sales" in lower else "general")
    learned_rules = [r for r in (memory or []) if r.get("topic") == topic]
    if kind in {"decision", "ambient"}:
        options = [{"id": "maintain", "label": "Maintain current allocation", "type": "option"}, {"id": "shift", "label": "Shift allocation to Supplier B", "type": "option"}]
        specs = [("unit_cost", "Unit cost", "known", "erp-supplier-master", False),
                 ("peak_capacity", "Q4 peak capacity", "unknown", "ops-capacity-plan", False),
                 ("lead_time", "Lead-time distribution", "unknown", "ops-capacity-plan", False),
                 ("defect_rate", "Defect rate", "unknown", "quality-scorecard", False),
                 ("minimum_order", "Minimum order quantity", "assumed", "erp-supplier-master", False),
                 ("transition_cost", "Transition cost", "unknown", "erp-supplier-master", False)]
        for key, label, state, source, critical in specs:
            learned = [rule for rule in learned_rules if key.replace("_", " ") in rule.get("rule", "").casefold()]
            variables.append({"id": key, "label": label, "type": "variable", "state": state,
                              "state_label": STATE_LABELS[state],
                              "critical": critical or bool(learned), "blocks_choice": critical or bool(learned), "required": True, "source_id": source,
                              "note": "Prior outcomes indicate this variable can change supplier decisions." if learned else "",
                              "evidence": []})
    elif kind == "direct":
        variables = [{"id": "answer_source", "label": "Business records for this answer", "type": "source", "state": "unknown", "state_label": STATE_LABELS["unknown"], "critical": False, "blocks_choice": False, "required": True, "source_id": "crm-sales-quarterly", "evidence": []}]
    elif kind == "investigation":
        variables = [
            {"id": "observed_change", "label": "Measured sales change", "type": "variable", "state": "unknown", "state_label": STATE_LABELS["unknown"], "critical": True, "blocks_choice": True, "required": True, "source_id": "crm-sales-quarterly", "evidence": []},
            {"id": "channel_mix", "label": "Sales by channel", "type": "variable", "state": "unknown", "state_label": STATE_LABELS["unknown"], "critical": False, "blocks_choice": False, "required": True, "source_id": "crm-sales-quarterly", "evidence": []},
            {"id": "causes", "label": "Possible reasons", "type": "variable", "state": "assumed", "state_label": STATE_LABELS["assumed"], "critical": False, "blocks_choice": False, "required": True, "source_id": "market-index-demo", "note": "Possible reasons are guesses until another record supports them.", "evidence": []},
            {"id": "conflicts", "label": "Do records disagree?", "type": "variable", "state": "unknown", "state_label": STATE_LABELS["unknown"], "critical": False, "blocks_choice": False, "required": True, "source_id": "crm-sales-quarterly", "note": "Records have not been compared yet.", "evidence": []},
        ]
    else:
        variables = [
            {"id": "criteria", "label": "Requirements from your request", "type": "spec", "state": "known", "state_label": STATE_LABELS["spec"], "critical": False, "blocks_choice": False, "required": True, "source_id": None, "evidence": []},
            {"id": "manufacturer_dataset", "label": "Matching manufacturer list", "type": "dataset", "state": "unknown", "state_label": STATE_LABELS["dataset"], "critical": False, "blocks_choice": False, "required": True, "source_id": "market-index-demo", "evidence": []},
        ]

    skipped = ["08"] if kind in {"direct", "investigation", "data"} else []
    steps = [
        {"id": "01", "name": "Parse", "status": "complete", "detail": "Entities, intent, constraints and time horizon extracted."},
        {"id": "02", "name": "Classify", "status": "complete", "detail": kind},
        {"id": "03", "name": "Represent", "status": "complete", "detail": f"{len(variables)} required variables; {len(options)} alternatives."},
        {"id": "04", "name": "Map context", "status": "complete", "detail": "Matched only permitted local organization fixtures."},
        {"id": "05", "name": "Find gaps", "status": "complete", "detail": f"{sum(v['state'] == 'unknown' for v in variables)} unknown; {sum(v['state'] == 'assumed' for v in variables)} assumed; {sum(v['state'] == 'conflicting' for v in variables)} conflicting."},
        {"id": "06", "name": "Plan acquisition", "status": "planned", "detail": "Acquire only required variables from their mapped permitted source."},
        {"id": "07", "name": "Construct", "status": "planned", "detail": {"direct": "Grounded answer", "investigation": "Evidence-led analysis", "decision": "Decision graph and state", "ambient": "Consent-gated decision graph", "data": "Normalized constrained dataset"}[kind]},
        {"id": "08", "name": "Persist", "status": "skipped" if "08" in skipped else "planned", "detail": "No consequential decision state to persist." if "08" in skipped else "Save the open decision and later compare its outcome."},
    ]
    mission_id = "M-" + uuid.uuid4().hex[:8].upper()
    return {
        "id": mission_id, "prompt": text, "channel": channel, "type": kind,
        "title": "Supplier allocation" if is_supplier else text[:72], "topic": topic,
        "status": "blocked" if kind in {"decision", "ambient"} else "open",
        "status_label": STATUS_LABELS["blocked" if kind in {"decision", "ambient"} else "open"],
        "type_label": TYPE_LABELS[kind],
        "created_at": now(), "updated_at": now(),
        "spec": {"object": "supplier allocation" if is_supplier else ("sales" if "sales" in lower else "requested information"),
                 "outcome": {"direct": "answer", "investigation": "explain with evidence", "decision": "decision support", "ambient": "decision support", "data": "structured dataset"}[kind],
                 "constraints": constraints, "geography": geography,
                 "time_horizon": f"Q{quarter.group(1)} {quarter.group(2) or '2026'}" if quarter else None,
                 "certainty_required": "source-backed"},
        "variables": variables, "options": options, "workflow": steps,
        "memory_context": [{"rule": r["rule"], "support_count": r["support_count"]} for r in learned_rules],
        "result": None, "decision": None,
    }
