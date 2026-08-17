# Deliverability Service

Responsibility: inbox placement testing, deliverability guidance, and seed-account analysis.

Intended for operator-owned seed accounts only in later phases.

Planned clean-architecture layout:
- `domain`: deliverability scorecards and inbox result models
- `application`: seed test orchestration and analysis flows
- `infrastructure`: IMAP/provider integrations
- `interfaces`: API/worker triggers and reports
