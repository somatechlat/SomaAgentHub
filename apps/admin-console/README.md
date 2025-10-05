# SomaGent Admin Console

**Sprint-4: Experience & Ecosystem**

React-based admin console for managing SomaGent models, providers, and marketplace capsules.

## Features

- **Overview Dashboard**: Platform health, active sessions, token usage metrics
- **Models & Providers**: Configure model profiles and view token forecasts
- **Marketplace**: Browse and manage task capsules with compliance badges

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **Tailwind CSS** for styling
- **React Router** for navigation

## Development

```bash
# Install dependencies
cd apps/admin-console
pnpm install  # or npm install / yarn

# Start development server
pnpm dev

# Build for production
pnpm build

# Type-check
pnpm type-check

# Lint
pnpm lint
```

The app runs on `http://localhost:3000` and proxies API calls to backend services on port 8000.

## Sprint Integration

- Aligns with **Parallel_Backlog.md** Sprint-4 deliverables
- Consumes live settings API from Identity & Settings squad
- Integrates token forecasts from Token Estimator service (to be implemented)
- Ready for contract recording via `scripts/parallel/record_contracts.py`

## Status

🟡 **In Progress** - Scaffold complete; wiring live APIs next

See `docs/sprints/Parallel_Backlog.md` for task tracking.
