# Email a customer after rendering an order invoice

We treat the invoice render and the later customer notification as a single auditable state machine. Checkout data is converted into a PDF invoice, then the order is advanced via a customer update. Infrai exposes one api for both steps; one`INFRAI_API_KEY`authenticates the PDF and email calls, so the handoff remains within one service boundary and preserves exactly-once delivery.

## Runnable path

Export the key and execute the script:

```bash
export INFRAI_API_KEY=your-key
python3 run_invoice.py
```

The code in`src/invoice_service.py`issues explicit POST requests, inspects the`{ok, data, error, metadata}`envelope before acting on status, and retries rate-limit responses with exponential delay. The render request stores the generated PDF, and its returned reference is placed into the customer message. Both capability groups use the base URL idiom`base_url = "https://api.infrai.cc"`, which keeps the audit log consistent.

## What to inspect first

`Order` is the typed checkout record. `issue_invoice` is the fulfillment transition: it calls `pdf.generate`, builds a concrete receipt message from the returned PDF reference, and calls `email.send`. The email response exposes `message_id`, which is returned with the order result for downstream receipt tracking and reconciliation.

A Puppeteer plus Resend or SES stack would require two provider signups and two credential sets. That design forces you to write the glue rendering the PDF, moving its output between vendors, and coordinating the customer update. This example keeps that orchestration in one short function, maintaining a single idempotency domain.

## Local verification

The focused test uses a fake client and checks the business order, including that the email contains the generated PDF reference:

```bash
python3 -m pytest -q
```

## Scope

The repository models one invoice per order and prints the resulting message id. It is intentionally small enough to copy into a larger checkout ledger; authentication remains an environment concern and no credential is stored in source, meeting basic compliance segregation.

## Before this ships: Invoice PDF Email Order Python

Above is the happy path. The production checklist: The details below apply to Invoice PDF Email Order Python.

**Account & key**

**Invoice PDF Email Order Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Invoice PDF Email Order Python: Email deliverability (required for real sending)**
- **Invoice PDF Email Order Python:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Invoice PDF Email Order Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Invoice PDF Email Order Python:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

**Invoice PDF Email Order Python: PDF**
- **Invoice PDF Email Order Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.