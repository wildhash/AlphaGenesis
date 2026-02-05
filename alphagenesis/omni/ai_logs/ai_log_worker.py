import json
import random
import threading
import time
from typing import Any, Dict
from loguru import logger

from .ai_log_store import AILogStore
from .ai_log_uploader import AILogUploader


class AILogWorker:
    def __init__(
        self,
        store: AILogStore,
        uploader: AILogUploader,
        poll_interval: float = 2.0,
        max_backoff: int = 60,
        max_attempts: int = 30,
        log_every_seconds: int = 300,
    ):
        self.store = store
        self.uploader = uploader
        self.poll_interval = poll_interval
        self.max_backoff = max_backoff
        self.max_attempts = max_attempts
        self.log_every_seconds = log_every_seconds
        self._thread = None
        self._running = False
        self._last_log_ts = 0.0
        self._last_success_ts = 0.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while self._running:
            try:
                event = self.store.claim_next()
                if not event:
                    self._maybe_log_queue()
                    time.sleep(self.poll_interval)
                    continue

                payload = json.loads(event["payload_json"])
                success, response = self.uploader.upload(payload)

                if success:
                    self.store.mark_done(event["id"])
                    self._last_success_ts = time.time()
                else:
                    self._handle_failure(event, response)
            except Exception as e:
                logger.warning("AI log worker error: {}", e)
                time.sleep(self.poll_interval)

    def _handle_failure(self, event: Dict[str, Any], response: Dict[str, Any]) -> None:
        attempts = int(event.get("attempts", 1))
        error = str(response)[:500] if response is not None else "unknown"

        if attempts >= self.max_attempts:
            self.store.mark_dead(event["id"], error)
            return

        backoff = min(self.max_backoff, 2 ** attempts)
        jitter = random.uniform(0.5, 1.5)
        next_attempt = int(time.time() * 1000 + backoff * 1000 * jitter)
        self.store.mark_retry(event["id"], next_attempt, error)

    def _maybe_log_queue(self) -> None:
        now = time.time()
        if now - self._last_log_ts < self.log_every_seconds:
            return
        pending = self.store.pending_count()
        last_success = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._last_success_ts))
            if self._last_success_ts else "never"
        )
        logger.info(
            "AI log queue status: pending={}, last_success={}",
            pending,
            last_success,
        )
        self._last_log_ts = now
