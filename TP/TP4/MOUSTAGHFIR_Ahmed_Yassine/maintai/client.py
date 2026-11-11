"""Client Python de l'API MaintAI.

Les tests passent leur propre client HTTP (celui de FastAPI) via http=.
"""

from __future__ import annotations

import httpx


class APIError(Exception):
    """L'API a répondu, mais pas 200."""

    def __init__(self, status_code: int, detail: object) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")


class MaintaiClient:
    def __init__(
        self,
        api_key: str | None = None,
        http: httpx.Client | None = None,
        base_url: str = "http://127.0.0.1:8000",
    ) -> None:
        self.api_key = api_key or None
        self.http = http or httpx.Client(base_url=base_url)

    def predict(self, reading: dict) -> dict:
        """POST /v1/predict. Lève APIError si le code n'est pas 200."""
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        reponse = self.http.post("/v1/predict", json=reading, headers=headers)
        if reponse.status_code != 200:
            raise APIError(reponse.status_code, reponse.json().get("detail"))
        return reponse.json()
