# Imports Service

Responsibility: contact import pipelines, file parsing, validation, and error reporting.

Planned clean-architecture layout:
- `domain`: import job state and row validation rules
- `application`: mapping, parsing, and commit workflows
- `infrastructure`: file readers and storage adapters
- `interfaces`: upload endpoints and worker hooks
