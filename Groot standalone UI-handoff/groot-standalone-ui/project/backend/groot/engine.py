"""Mission execution, source acquisition, decision-state and learning rules."""
from __future__ import annotations

from typing import Any

from . import seed
from .compiler import STATE_LABELS, STATUS_LABELS, now
from .store import Store


def _variable(mission: dict, variable_id: str) -> dict:
    for item in mission.get("variables", []):
        if item["id"] == variable_id:
            return item
    raise KeyError(f"Variable '{variable_id}' is not part of mission {mission['id']}.")


def refresh_status(mission: dict) -> dict:
    if mission["type"] not in {"decision", "ambient"}:
        mission["status"] = "awaiting_input" if mission.get("result", {}).get("needs_clarification") else ("complete" if mission.get("result") else "open")
    else:
        unknown = [v for v in mission["variables"] if v["type"] == "variable" and v["state"] in {"unknown", "acquiring"}]
        mission["status"] = "blocked" if any(v.get("critical") for v in unknown) else ("open" if unknown else "ready")
    mission["status_label"] = STATUS_LABELS[mission["status"]]
    for variable in mission.get("variables", []):
        variable["state_label"] = STATE_LABELS.get(variable["state"], variable["state"])
        variable["blocks_choice"] = bool(variable.get("critical"))
    return mission


def execute(store: Store, mission: dict) -> dict:
    kind, spec = mission["type"], mission["spec"]
    if kind == "direct":
        region = spec.get("geography")
        quarter = spec.get("time_horizon")
        if not region or not quarter:
            missing = [name for name, value in (("region", region), ("quarter or time period", quarter)) if not value]
            mission["result"] = {"needs_clarification": True, "question": "Which " + " and ".join(missing) + " should I use?", "missing": missing, "limitations": ["GROOT does not guess omitted query filters."]}
            v = mission["variables"][0]
            v["state"] = "unknown"
        else:
            rows = [row for row in seed.SALES if row["region"].casefold() == region.casefold() and row["quarter"].casefold() == quarter.casefold()]
            if not rows:
                mission["result"] = {"answer": f"No matching {quarter} sales rows were found for {region} in the connected ledger.", "records": [], "limitations": ["This answer covers the seeded quarterly sales ledger only."]}
            else:
                total = round(sum(row["revenue_lakh_inr"] for row in rows), 2)
                mission["result"] = {"answer": f"{quarter} sales in {region} were ₹{total:,.2f} lakh across {sum(row['orders'] for row in rows):,} orders.", "revenue_lakh_inr": total, "orders": sum(row["orders"] for row in rows), "breakdown": rows, "sources": ["crm-sales-quarterly"], "limitations": ["Demo organization fixture; amounts are illustrative."]}
                v = mission["variables"][0]
                v["state"] = "known"
                ev = store.add_evidence(mission["id"], v["id"], "crm-sales-quarterly", f"Quarterly ledger sum for {region}, {quarter}", mission["result"], 0.99, {"adapter": "sales-ledger-fixture", "record_count": len(rows), "filters": {"region": region, "quarter": quarter}})
                v["evidence"].append(ev)
    elif kind == "investigation":
        region = spec.get("geography")
        quarter = spec.get("time_horizon")
        if not region or not quarter:
            missing = [name for name, value in (("region", region), ("quarter or time period", quarter)) if not value]
            mission["result"] = {"needs_clarification": True, "question": "Which " + " and ".join(missing) + " should I investigate?", "missing": missing, "limitations": ["GROOT does not infer an omitted investigation scope."]}
        else:
            qmatch = __import__("re").search(r"Q([1-4])", quarter)
            prior = f"Q{max(1, int(qmatch.group(1)) - 1)} 2026" if qmatch else "Q1 2026"
            rows = [r for r in seed.SALES if r["region"].casefold() == region.casefold() and r["quarter"] in {prior, quarter}]
            sums = {q: round(sum(r["revenue_lakh_inr"] for r in rows if r["quarter"] == q), 2) for q in (prior, quarter)}
            change = round((sums[quarter] - sums[prior]) / sums[prior] * 100, 1) if sums.get(prior) else None
            old_channel = {r["channel"]: r["revenue_lakh_inr"] for r in rows if r["quarter"] == prior}
            new_channel = {r["channel"]: r["revenue_lakh_inr"] for r in rows if r["quarter"] == quarter}
            deltas = [{"channel": channel, "prior_lakh_inr": old_channel.get(channel, 0), "current_lakh_inr": new_channel.get(channel, 0), "change_lakh_inr": round(new_channel.get(channel, 0) - old_channel.get(channel, 0), 2)} for channel in sorted(set(old_channel) | set(new_channel))]
            mission["result"] = {"observation": f"{region} sales changed {change:+.1f}% from {prior} to {quarter}." if change is not None else f"Insufficient comparable rows for {region}.", "prior_quarter": prior, "current_quarter": quarter, "prior_revenue_lakh_inr": sums.get(prior), "current_revenue_lakh_inr": sums.get(quarter), "change_pct": change, "channel_deltas": deltas, "hypotheses": [{"statement": "The decline is concentrated in the partner channel.", "status": "supported_by_observation" if any(d["channel"] == "Partner" and d["change_lakh_inr"] < 0 for d in deltas) else "unverified", "causal_claim": False}, {"statement": "Pricing, seasonality or competitor changes caused the decline.", "status": "unverified", "causal_claim": False}], "sources": ["crm-sales-quarterly"], "limitations": ["The fixture supports quarter and channel comparisons, not causal attribution."]}
            for v in mission["variables"]:
                if v["id"] in {"observed_change", "channel_mix", "conflicts"} and rows:
                    v["state"] = "known"
                    ev = store.add_evidence(mission["id"], v["id"], "crm-sales-quarterly", v["label"], mission["result"], 0.96, {"adapter": "sales-ledger-fixture", "record_count": len(rows), "filters": {"region": region, "quarters": [prior, quarter]}})
                    v["evidence"].append(ev)
    elif kind == "data":
        constraints = {c["type"]: c["value"] for c in spec.get("constraints", [])}
        limit = min(100, max(1, constraints.get("limit", 25)))
        minimum = constraints.get("min_monthly_capacity", 0)
        certification = constraints.get("certification")
        rows = [r for r in seed.MANUFACTURERS if r["capacity_units_month"] >= minimum and (not certification or certification in r["certifications"])]
        mission["result"] = {"count": min(limit, len(rows)), "total_matches": len(rows), "constraints": constraints, "fields": ["name", "city", "state", "category", "certifications", "capacity_units_month", "lead_days"], "rows": rows[:limit], "sources": ["market-index-demo"], "limitations": ["Synthetic approved-source fixture; verify all vendors before procurement use."]}
        v = _variable(mission, "manufacturer_dataset")
        v["state"] = "known"
        ev = store.add_evidence(mission["id"], v["id"], "market-index-demo", "Constraint-filtered manufacturer fixture", mission["result"], 0.9, {"adapter": "manufacturer-catalog-fixture", "candidate_count": len(seed.MANUFACTURERS), "returned_count": min(limit, len(rows)), "filters": constraints})
        v["evidence"].append(ev)
    else:
        cost_node = next((v for v in mission.get("variables", []) if v["id"] == "unit_cost" and v["state"] == "known" and not v.get("evidence")), None)
        if cost_node:
            supplier_a = seed.SUPPLIERS[0]
            supplier_b = seed.SUPPLIERS[1]
            savings = round((supplier_a["unit_cost"] - supplier_b["unit_cost"]) / supplier_a["unit_cost"] * 100, 1)
            value = {"supplier_a_usd": supplier_a["unit_cost"], "supplier_b_usd": supplier_b["unit_cost"], "b_savings_pct": savings, "currency": "USD"}
            ev = store.add_evidence(mission["id"], cost_node["id"], cost_node["source_id"], "Supplier B unit-cost comparison from current supplier master", value, 0.97, {"adapter": "supplier-master-fixture", "source_id": cost_node["source_id"], "scope": "simulated evidence"})
            cost_node["evidence"].append(ev)
        mission["decision"] = {"state": "blocked", "state_label": STATUS_LABELS["blocked"], "recommendation": None, "reason": "A person should wait until the important missing facts are checked.", "open_gaps": [v["id"] for v in mission["variables"] if v.get("critical") and v["state"] != "known"]}
    for step in mission.get("workflow", []):
        if step["id"] in {"06", "07"}:
            step["status"] = "complete"
            step["detail"] = "Executed against the mapped local fixture; source lineage recorded."
    refresh_status(mission)
    store.log(mission["id"], "mission.executed", {"type": kind, "status": mission["status"]})
    return store.save_mission(mission)


def acquire(store: Store, mission: dict, variable_id: str) -> dict:
    variable = _variable(mission, variable_id)
    if variable["type"] in {"option", "spec", "dataset"} or variable["state"] == "known":
        raise ValueError("This graph item does not need evidence acquisition.")
    source_id = variable.get("source_id")
    if not source_id or not any(s["id"] == source_id and s["permitted"] for s in seed.SOURCES):
        raise ValueError("No permitted source is mapped to this variable.")
    data: dict[str, Any]
    supplier_b = next(s for s in seed.SUPPLIERS if s["id"] == "SUP-B")
    if variable_id == "unit_cost":
        supplier_a = seed.SUPPLIERS[0]
        saving = round((supplier_a["unit_cost"] - supplier_b["unit_cost"]) / supplier_a["unit_cost"] * 100, 1)
        data = {"supplier_a_usd": supplier_a["unit_cost"], "supplier_b_usd": supplier_b["unit_cost"], "b_savings_pct": saving, "currency": "USD"}
    elif variable_id == "peak_capacity":
        supplier_a = seed.SUPPLIERS[0]
        headroom = supplier_b["q4_capacity_units"] - supplier_b["q4_commitment_units"]
        percent = next((c["value"] for c in mission["spec"].get("constraints", []) if c["type"] == "allocation_percent"), None)
        shifted_units = round(supplier_a["q4_commitment_units"] * percent / 100) if percent is not None else None
        shortfall = max(0, shifted_units - headroom) if shifted_units is not None else None
        data = {"supplier": supplier_b["name"], "q4_capacity_units": supplier_b["q4_capacity_units"], "q4_committed_units": supplier_b["q4_commitment_units"], "headroom_units": headroom, "supplier_a_current_q4_units": supplier_a["q4_commitment_units"], "proposed_shift_pct": percent, "proposed_shift_units": shifted_units, "projected_b_load_units": supplier_b["q4_commitment_units"] + shifted_units if shifted_units is not None else None, "projected_shortfall_units": shortfall, "capacity_check": "shortfall" if shortfall else "within_capacity" if shifted_units is not None else "needs_shift_percent", "calculation_note": "Estimate uses current sample commitments and assumes the requested percentage applies to Supplier A's Q4 committed units.", "period": "Q4 2026"}
    elif variable_id == "lead_time":
        data = {"supplier": supplier_b["name"], "p50_days": supplier_b["lead_days_p50"], "p90_days": supplier_b["lead_days_p90"], "period": "trailing 12 months"}
    elif variable_id == "defect_rate":
        data = {"supplier": supplier_b["name"], "defect_rate_pct": supplier_b["defect_rate_pct"], "on_time_delivery_pct": supplier_b["on_time_pct"], "period": "trailing 12 months"}
    elif variable_id == "minimum_order":
        data = {"supplier": supplier_b["name"], "minimum_order_units": supplier_b["moq"], "contract_status": "current ERP export"}
    elif variable_id == "transition_cost":
        data = {"supplier": supplier_b["name"], "estimated_one_time_usd": supplier_b["transition_cost"], "status": "planning estimate"}
    elif variable_id == "answer_source":
        raise ValueError("Use mission execution to answer direct questions.")
    elif variable_id == "observed_change":
        raise ValueError("Use mission execution to acquire the sales comparison.")
    elif variable_id in {"channel_mix", "causes", "conflicts"}:
        raise ValueError("Use mission execution to acquire investigation context.")
    else:
        raise ValueError("This variable has no fixture adapter yet.")
    confidence = 0.95 if variable_id == "peak_capacity" else (0.88 if variable_id == "transition_cost" else 0.97)
    claim = f"{variable['label']} retrieved from permitted source {source_id}."
    lineage = {"adapter": "seeded-organization-fixture", "source_id": source_id, "source_updated_at": next(s["updated_at"] for s in seed.SOURCES if s["id"] == source_id), "scope": "simulated evidence; no external system was contacted"}
    evidence = store.add_evidence(mission["id"], variable_id, source_id, claim, data, confidence, lineage)
    variable["state"] = "known"
    variable["evidence"].append(evidence)
    variable["note"] = "Evidence is attached with source, retrieval time and confidence."
    for step in mission.get("workflow", []):
        if step["id"] == "06":
            step["status"] = "complete"
            step["detail"] = f"Acquired {variable['label']} from {source_id}."
    refresh_status(mission)
    if mission["type"] in {"decision", "ambient"} and mission["status"] == "ready":
        mission["decision"] = {"state": "ready", "state_label": STATUS_LABELS["ready"], "recommendation": None, "reason": "The listed facts have been checked. A person still chooses what to do.", "open_gaps": []}
    store.log(mission["id"], "evidence.acquired", {"variable_id": variable_id, "source_id": source_id, "confidence": confidence})
    store.save_mission(mission)
    return {"mission": mission, "evidence": evidence}


def save_decision(store: Store, mission: dict, choice: str, rationale: str) -> dict:
    if mission["type"] not in {"decision", "ambient"}:
        raise ValueError("Only decision missions can be saved as decisions.")
    refresh_status(mission)
    if mission["status"] != "ready":
        raise ValueError("Resolve all unknown variables before saving this decision.")
    allowed = {o["label"] for o in mission.get("options", [])}
    if not choice.strip() or len(choice) > 180:
        raise ValueError("A decision choice of at most 180 characters is required.")
    if allowed and choice not in allowed:
        allowed_text = "; ".join(sorted(allowed))
        raise ValueError(f"Choice must match a modeled option: {allowed_text}")
    mission["decision"] = {"state": "saved", "state_label": STATUS_LABELS["saved"], "choice": choice, "rationale": rationale[:1000], "recorded_at": now(), "evidence_snapshot": [e for v in mission["variables"] for e in v.get("evidence", [])]}
    mission["status"] = "saved"
    store.log(mission["id"], "decision.saved", {"choice": choice, "rationale": rationale[:300]})
    return store.save_mission(mission)


def record_outcome(store: Store, mission: dict, observed: str) -> dict:
    if mission["status"] != "saved" or not mission.get("decision"):
        raise ValueError("Save a decision before recording its outcome.")
    if not observed.strip() or len(observed) > 1200:
        raise ValueError("An observed outcome of at most 1,200 characters is required.")
    outcome = store.record_outcome(mission["id"], mission["topic"], mission["decision"]["choice"], observed.strip())
    mission["outcome"] = outcome
    mission["status"] = "learned"
    store.log(mission["id"], "outcome.recorded", outcome)
    store.save_mission(mission)
    return {"mission": mission, "outcome": outcome}


def classify_room(text: str) -> dict:
    low = text.casefold()
    if any(term in low for term in ("don't have", "do not have", "no evidence", "unknown", "not confirmed", "don't know")):
        return {"signal": "unknown", "node_id": "peak_capacity", "claim": "A decision-relevant fact is missing", "detail": "Unresolved evidence gap detected."}
    if any(term in low for term in ("worried", "concern", "risk", "objection")):
        return {"signal": "objection", "node_id": "peak_capacity", "claim": "A participant raised a decision risk", "detail": "Concern captured; it is not treated as a verified fact."}
    if any(term in low for term in ("let's", "lets", "decide", "hold", "wait until")):
        return {"signal": "decision", "node_id": "decision", "claim": "A decision or commitment was stated", "detail": "Meeting signal; participant confirmation may still be required."}
    return {"signal": "known", "node_id": "unit_cost", "claim": "A factual statement was raised", "detail": "Captured as a meeting claim; verify against an evidence source."}


def record_room_statement(store: Store, mission: dict, session_id: str, speaker: str, text: str, signal: dict | None = None) -> dict:
    signal = signal or classify_room(text)
    mission_id = mission["id"]
    event = store.room_event(session_id, mission_id, speaker, text, signal["signal"])
    mission.setdefault("room_events", []).append({**event, **signal})
    target = next((v for v in mission.get("variables", []) if v["id"] == signal.get("node_id")), None)
    if target and signal["signal"] == "unknown":
        target["state"] = "unknown"
        target["critical"] = True
        target["note"] = "A participant raised an important missing fact. Check a source before relying on it."
    elif target and signal["signal"] in {"objection", "known"}:
        target.setdefault("meeting_claims", []).append({"text": text, "speaker": speaker, "signal": signal["signal"], "captured_at": event["created_at"], "verified": False})
    refresh_status(mission)
    store.log(mission_id, "decision_room.signal_detected", {"session_id": session_id, "signal": signal["signal"], "node_id": signal.get("node_id")})
    store.save_mission(mission)
    return {"event": {**event, **signal}, "mission": mission, "response": "GROOT found a statement that may affect this choice. The statement is saved as unconfirmed until a sample record supports it."}
