import json
from typing import Any, Dict, Optional
from loguru import logger

from .ai_log_store import AILogStore


class AILogBus:
    def __init__(self, store: AILogStore):
        self.store = store

    def emit(
        self,
        stage: str,
        model: str,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        explanation: str,
        order_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            safe_input = self._ensure_json(input_payload)
            safe_output = self._ensure_json(output_payload)
            safe_explanation = (explanation or "")[:1000]
            return self.store.enqueue(
                stage=stage,
                model=model,
                input_payload=safe_input,
                output_payload=safe_output,
                explanation=safe_explanation,
                order_id=order_id,
                meta=meta,
            )
        except Exception as e:
            logger.warning("AI log emit failed: {}", e)
            return None

    def _ensure_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json.dumps(payload, ensure_ascii=True, default=str)
            return payload
        except Exception:
            return {"payload": str(payload)[:1000]}
