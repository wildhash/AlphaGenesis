import json
from typing import Any, Dict, Optional
from loguru import logger

try:
    import numpy as np
except Exception:
    np = None

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

    def _sanitize_payload(self, payload: Any) -> Any:
        if payload is None:
            return None
        if isinstance(payload, (str, int, float, bool)):
            return payload
        if np is not None:
            if isinstance(payload, np.generic):
                try:
                    return payload.item()
                except Exception:
                    return str(payload)
            if isinstance(payload, np.ndarray):
                return [self._sanitize_payload(x) for x in payload.tolist()]
        if isinstance(payload, dict):
            return {str(k): self._sanitize_payload(v) for k, v in payload.items()}
        if isinstance(payload, (list, tuple, set)):
            return [self._sanitize_payload(v) for v in payload]
        try:
            return str(payload)
        except Exception:
            return repr(payload)

    def _ensure_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            safe_payload = self._sanitize_payload(payload)
            json.dumps(safe_payload, ensure_ascii=True, default=str)
            return safe_payload
        except Exception:
            return {"payload": str(payload)[:1000]}
