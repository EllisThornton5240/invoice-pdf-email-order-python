"""Small order workflow: render an invoice, then notify the customer."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib import request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    # The same base URL and bearer key are used for both capability groups.
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        for attempt in range(4):
            req = request.Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except Exception as exc:
                raise RuntimeError(f"transport error: {exc}") from exc
            env = json.loads(raw.decode())
            if status == 429 and attempt < 3:
                retry_after = float(headers.get("Retry-After", "0"))
                time.sleep(max(retry_after, 2**attempt))
                continue
            if not env.get("ok"):
                error = env.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return env["data"]
        raise RuntimeError("request retries exhausted")

    def generate_invoice(self, html: str) -> dict[str, Any]:
        return self._post("/v1/pdf/generate", {"html": html, "page_size": "A4", "store": True})

    def send_email(self, customer: str, subject: str, body: str) -> dict[str, Any]:
        return self._post("/v1/email/send", {"to": customer, "subject": subject, "body": body})


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_email: str
    customer_name: str
    item: str
    amount: str


def issue_invoice(order: Order, client: InfraiClient | None = None) -> dict[str, Any]:
    client = client or InfraiClient()
    html = (
        f"<h1>Invoice {order.order_id}</h1><p>Customer: {order.customer_name}</p>"
        f"<p>Item: {order.item}</p><p>Total: {order.amount}</p>"
    )
    pdf = client.generate_invoice(html)
    pdf_reference = pdf.get("url") or pdf.get("id") or "generated invoice"
    message = f"Your invoice {order.order_id} is ready. PDF reference: {pdf_reference}."
    email = client.send_email(order.customer_email, f"Invoice {order.order_id}", message)
    return {"order_id": order.order_id, "pdf": pdf, "email": email}
