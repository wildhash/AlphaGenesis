import time

from alphagenesis.omni.ai_logs import AILogStore


def test_ai_log_store_roundtrip(tmp_path):
    db_path = tmp_path / "ai_logs.sqlite"
    store = AILogStore(str(db_path))

    event_id = store.enqueue(
        stage="Decision",
        model="unit",
        input_payload={"x": 1},
        output_payload={"y": 2},
        explanation="unit test",
    )

    event = store.claim_next()
    assert event is not None
    assert event["id"] == event_id

    future_ms = int(time.time() * 1000) + 1000
    store.mark_retry(event_id, future_ms, "retry")

    pending = store.pending_count()
    assert pending >= 1

    store.mark_done(event_id)
    assert store.pending_count() == 0
