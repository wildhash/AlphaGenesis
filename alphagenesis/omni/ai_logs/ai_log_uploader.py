from typing import Any, Dict, Tuple


class AILogUploader:
    def __init__(self, weex_client, endpoint: str = "/capi/v2/order/uploadAiLog"):
        self.weex = weex_client
        self.endpoint = endpoint

    def upload(self, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        response = self.weex._request("POST", self.endpoint, data=payload, signed=True)
        code = response.get("code") if isinstance(response, dict) else None
        success = code == "00000"
        return success, response
