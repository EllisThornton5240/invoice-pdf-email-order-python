from src.invoice_service import Order, issue_invoice


class FakeClient:
    def __init__(self):
        self.calls = []

    def generate_invoice(self, html):
        self.calls.append(("pdf", html))
        return {"url": "https://files.example/invoice.pdf"}

    def send_email(self, customer, subject, text):
        self.calls.append(("email", customer, subject, text))
        return {"message_id": "msg-1"}


def test_invoice_render_precedes_customer_update():
    fake = FakeClient()
    result = issue_invoice(Order("ORD-7", "buyer@example.com", "Lin", "Notebook", "USD 12.00"), fake)
    assert result["email"]["message_id"] == "msg-1"
    assert fake.calls[0][0] == "pdf"
    assert fake.calls[1][0] == "email"
    assert "https://files.example/invoice.pdf" in fake.calls[1][3]
