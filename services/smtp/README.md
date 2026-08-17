# SMTP Service

Responsibility: SMTP provider orchestration, connection management, throttling, and queued send execution.

Planned clean-architecture layout:
- `domain`: provider policies, message lifecycle rules
- `application`: send orchestration and retry policies
- `infrastructure`: SMTP client adapters and credential access
- `interfaces`: worker/API entry points
