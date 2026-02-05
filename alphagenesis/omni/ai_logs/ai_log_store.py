import json
import os
import sqlite3
import time
import uuid
from typing import Any, Dict, Optional


class AILogStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_logs (
                    id TEXT PRIMARY KEY,
                    created_at_ms INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    model TEXT NOT NULL,
                    order_id TEXT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    next_attempt_at_ms INTEGER NOT NULL,
                    last_error TEXT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_logs_status_next ON ai_logs(status, next_attempt_at_ms)"
            )

    def enqueue(
        self,
        stage: str,
        model: str,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        explanation: str,
        order_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        event_id = str(uuid.uuid4())
        payload = {
            "stage": stage,
            "model": model,
            "input": input_payload,
            "output": output_payload,
            "explanation": explanation,
        }
        if order_id is not None:
            payload["orderId"] = str(order_id)
        if meta:
            payload["meta"] = meta
        now_ms = int(time.time() * 1000)
        payload_json = json.dumps(payload, ensure_ascii=True, default=str)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_logs (
                    id, created_at_ms, stage, model, order_id,
                    payload_json, status, attempts, next_attempt_at_ms, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    now_ms,
                    stage,
                    model,
                    str(order_id) if order_id is not None else None,
                    payload_json,
                    "pending",
                    0,
                    now_ms,
                    None,
                ),
            )
        return event_id

    def claim_next(self) -> Optional[Dict[str, Any]]:
        now_ms = int(time.time() * 1000)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT * FROM ai_logs
                WHERE status IN ('pending','retry')
                  AND next_attempt_at_ms <= ?
                ORDER BY created_at_ms ASC
                LIMIT 1
                """,
                (now_ms,),
            ).fetchone()

            if row is None:
                conn.commit()
                return None

            attempts = int(row["attempts"]) + 1
            conn.execute(
                """
                UPDATE ai_logs
                SET status = 'in_progress', attempts = ?, last_error = NULL
                WHERE id = ?
                """,
                (attempts, row["id"]),
            )
            conn.commit()

            data = dict(row)
            data["attempts"] = attempts
            return data

    def mark_done(self, event_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE ai_logs SET status = 'done' WHERE id = ?",
                (event_id,),
            )

    def mark_retry(self, event_id: str, next_attempt_at_ms: int, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_logs
                SET status = 'retry', next_attempt_at_ms = ?, last_error = ?
                WHERE id = ?
                """,
                (next_attempt_at_ms, error[:500] if error else None, event_id),
            )

    def mark_dead(self, event_id: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_logs
                SET status = 'dead', last_error = ?
                WHERE id = ?
                """,
                (error[:500] if error else None, event_id),
            )

    def pending_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM ai_logs WHERE status IN ('pending','retry','in_progress')"
            ).fetchone()
            return int(row["cnt"]) if row else 0
