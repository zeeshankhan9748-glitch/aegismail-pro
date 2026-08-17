# AegisMail Pro Web

Next.js App Router frontend for the Phase 1 AegisMail Pro scaffold.

## Included in this phase

- enterprise-style application shell with collapsible sidebar and top navigation
- dark/light mode toggle via `next-themes`
- command palette stub using `cmdk`
- SMTP Providers page wired to the FastAPI backend
- React Hook Form + Zod create-provider form
- reusable data table with sorting, filtering, pagination, and column visibility
- Vitest + React Testing Library component test

## Local commands

```bash
npm ci
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
```

The app reads `NEXT_PUBLIC_API_BASE_URL` at build time for client-side API calls.
