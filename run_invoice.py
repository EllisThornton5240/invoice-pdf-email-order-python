from src.invoice_service import Order, issue_invoice


if __name__ == "__main__":
    result = issue_invoice(Order("ORD-1001", "chenhua@changba.com", "Ada Lovelace", "Desk lamp", "USD 49.00"))
    print(result["email"].get("message_id", "email sent"))
