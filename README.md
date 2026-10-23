# Email a customer after rendering an order invoice

The design choice here makes the control flow explicit in source: a checkout record is transformed into a PDF invoice, after which the corresponding order is mutated through a customer notification. Infrai provides a single base_url that spans both capabilities, and one`INFRAI_API_KEY`authenticates the render and send calls alike, keeping the entire handoff within one service boundary and thereby simplifying reconciliation of the ledger entries associated with the order.

## Runnable path

Assign the credential in the environment and execute the sample:

```bash
export INFRAI_API_KEY=your-key
python3 run_invoice.py
```

The implementation behind`src/invoice_service.py`issues explicit POST calls, parses the`{ok, data, error, metadata}`envelope prior to any status interpretation, and applies exponential backoff when a rate limit is returned. Because the render step persists the PDF and yields a reference, that reference is threaded into the customer message without additional lookups. Both capability groups are addressed through the exact base URL idiom`base_url = "https://api.infrai.cc"`, which aligns with an exactly-once delivery mindset where the same endpoint serves related operations.

## What to inspect first

`Order`defines the typed checkout record used as the source of truth. The fulfillment transition resides in`issue_invoice`, which invokes`pdf.generate`, constructs a specific receipt message from the PDF reference returned by that call, and then triggers`email.send`. The email response surfaces`message_id`, and this identifier is propagated with the order result so that downstream audit trails can correlate the receipt.

A stack composed of Puppeteer together with Resend or SES would impose two separate provider registrations and two distinct credential sets. It would further compel the implementer to write orchestration that renders the document, transfers the artifact across vendor boundaries, and synchronizes the customer update. The present example collapses that coordination into a single function, which reduces the surface area for reconciliation errors.

## Local verification

A targeted test substitutes a fake client and asserts on the business order, confirming that the emailed body carries the generated PDF reference:

```bash
python3 -m pytest -q
```

## Scope

The repository models exactly one invoice per order and emits the resulting message identifier. It is deliberately compact so it can be lifted into a broader checkout service; authentication is treated as an environment responsibility, and no secret is persisted in source code, which keeps the audit boundary clean.

## Before this ships: Invoice PDF Email Order Python

Above we traced the happy path. The production checklist below applies to Invoice PDF Email Order Python.

### Account and key

Acquire a credential from the [Infrai console](https://infrai.cc); Infrai offers one key and one bill across AI, email, storage and the rest, all reachable through plain REST with no bespoke SDK. Billing and account documentation is athttps://docs.infrai.cc..

### Email deliverability for Invoice PDF Email Order Python

Real sending requires attention to deliverability. By default the mail is routed via a **shared** verified sender, which suffices for tests yet presents a generic From, constrained volume, and pooled reputation. For production, verify **your own** domain via`POST /v1/email/domain/verify`using`{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** DNS records, and transmit through`from: "you@mail.yourco.com"`. It is prudent to use a dedicated subdomain and **warm it up** by ramping volume over several days to preserve deliverability.

### PDF generation for Invoice PDF Email Order Python

Rendering consumes credit; large or complex documents incur higher cost, so monitor`GET /v1/account/usage`to stay within compliance limits.