# Logging Service

Responsibility: audit trails, send logs, provider responses, and analytics-oriented event pipelines.

Planned clean-architecture layout:
- `domain`: event schemas and retention policies
- `application`: event query and export workflows
- `infrastructure`: log sinks and observability adapters
- `interfaces`: API/reporting surfaces
