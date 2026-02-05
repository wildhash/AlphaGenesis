#!/usr/bin/env python3
"""
Smoke test for WEEX AI log upload (no orders).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alphagenesis.data import WEEXClient
from alphagenesis.omni.ai_logs import AILogStore, AILogUploader


def main() -> int:
    db_path = os.getenv("AI_LOG_DB_PATH", "/opt/AlphaGenesis/tmp/ai_logs.sqlite")
    store = AILogStore(db_path)
    client = WEEXClient()
    uploader = AILogUploader(client)

    payload = {
        "stage": "Smoke Test",
        "model": "AlphaGenesis-SDM",
        "input": {"symbol": "cmt_dogeusdt", "note": "ai log smoke"},
        "output": {"status": "ok"},
        "explanation": "WEEX AI log smoke test entry.",
    }

    event_id = store.enqueue(
        stage=payload["stage"],
        model=payload["model"],
        input_payload=payload["input"],
        output_payload=payload["output"],
        explanation=payload["explanation"],
    )

    event = store.claim_next()
    if not event:
        print("No pending AI log events found")
        return 1

    data = json.loads(event["payload_json"])
    success, response = uploader.upload(data)
    if success:
        store.mark_done(event["id"])
    else:
        store.mark_retry(event["id"], int(event["created_at_ms"]) + 60000, str(response))

    print({"event_id": event_id, "success": success, "response": response})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
