# Planned Data Model Roadmap

Phase 1 includes the following tables and migration pattern:

- `users`
- `roles`
- `api_keys`
- `smtp_providers`
- `sender_identities`

Remaining planned tables for later phases:

- `templates`
- `template_versions`
- `contacts`
- `contact_lists`
- `contact_list_members`
- `suppression_entries`
- `campaigns`
- `campaign_recipients`
- `messages`
- `message_events`
- `inbox_checks`
- `import_jobs`
- `audit_logs`

The service packages in `/services` are intentionally stubbed with clean-architecture notes so future phases can expand each domain without reworking the monorepo layout.
