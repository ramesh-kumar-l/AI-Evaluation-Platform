"""Phase 1: every mutation is audited, and the hash chain is tamper-evident."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.audit_event import AuditEvent
from app.services import audit


def test_mutations_write_audit_events_and_chain_is_intact(client: TestClient) -> None:
    created = client.post("/providers", json={"name": "P", "kind": "ollama"})
    key = created.json()["entity_key"]
    client.post(f"/providers/{key}/versions", json={"name": "P", "kind": "ollama"})

    events = client.get("/audit/events", params={"entity_key": key}).json()
    assert {e["action"] for e in events} == {"create", "new_version"}
    assert all(e["hash"] for e in events)

    assert client.get("/audit/verify").json() == {"intact": True}


def test_tampering_breaks_the_chain(client: TestClient) -> None:
    client.post("/prompts", json={"name": "p", "template": "t"})

    # Mutate a stored event out-of-band; the recomputed chain must no longer verify.
    with SessionLocal() as db:
        event = db.query(AuditEvent).first()
        assert event is not None
        event.payload = {**event.payload, "tampered": True}
        db.commit()
        assert audit.verify_chain(db) is False
