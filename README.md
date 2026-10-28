# Client Onboarding & Signed Webhook Lab
**Independent educational demo. Not real client onboarding, payroll processing, or a production security implementation.**

Uses SQLite to track a fictional employer onboarding workflow; validates event-state transitions; verifies HMAC-SHA256 webhook signatures; records unique event IDs for retry idempotency; gates approval/rejection on reviewer authorization; reports aggregate counts without exposing client fields.

## Run
```bash
python -m pip install fastapi uvicorn pytest httpx
pytest -q
uvicorn onboarding:app --port 8102
```
Open `/docs`; create a case then use JSON for POST `/webhooks/events`. Calculate `x-demo-signature` as `onboarding.signature(body, onboarding.SECRET)`. `x-reviewer-token: local-reviewer-demo` is deliberately a local test stub, **not production authentication**. Replace all secrets, authorization, audit and persistence layers prior to any actual deployment.

## Workflow
`created -> documents_validated -> awaiting_review -> approved/rejected -> completed (if approved)`.

## Measurements to collect in a real pilot
Onboarding stage completion time, duplicate event rate, exceptions, SLA breaches and manual-review time. Never load payroll/HR personal information into this demonstration.

## Added Checkwriters fit demonstrations
Expanded with onboarding completion rates, synthetic SLA-violation flags and human escalation recommendations. This is not deployed or connected to actual clients.
