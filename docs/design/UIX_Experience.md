⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# SomaGent UI/Experience Blueprint

This document captures the foundations for the user experience tier across the operator console, conversational clients, and notification system.

## 1. Experience Pillars
- **Conversational Canvas**: Real-time chat/voice interface with transcript timeline, persona badges, tool call visualizations, and inline audit links.
- **Operations Dashboard**: High-level overview of active capsules, token budgets, moderation alerts, and model usage health; supports multi-tenant filtering.
- **Admin Console**: Configuration flows for identity, models (LLM/SLM/voice), tool adapters, budgets, deployment modes, and marketplace installs.
- **Notification Center**: Unified tray for system alerts (failures, approvals needed), capsule milestones, budget thresholds, and training events.

## 2. Front-End Technology Stack
- **Framework**: React + TypeScript with Vite for local development and SSR-ready Next.js optional for future SEO surfaces.
- **Styling**: Tailwind CSS + Radix UI primitives for accessibility; design tokens stored in JSON for tenant theming.
- **State/Data**: TanStack Query for server interactions, Zustand for local ephemeral state (e.g., active conversation view), Redux toolkit optional if global store grows.
- **Real-time**: WebSockets (Socket.IO or native browser WebSocket) driven by `conversation.events` and `notifications.events`; fall back to Server-Sent Events when needed.
- **Component Testing**: Playwright for end-to-end flows, React Testing Library for unit tests, Chromatic/Storybook for visual regression.

## 3. Notification System
- **Back-end Flow**: Services publish structured messages to Kafka topic `notifications.events` (types: `alert`, `review`, `success`, `budget`). Notification orchestrator aggregates, applies tenant/user preferences, and pushes to WebSocket hubs + email/SMS providers.
- **Preferences Storage**: `settings-service` maintains `notification_preferences` table keyed by `(tenant_id, user_id)` with channels, severity thresholds, quiet hours. Changes emit `settings.changed` events so hubs reload.
- **UI Presentation**: Bell/tray component with severity color coding, grouped by capsule/project. Supports quick actions (approve, snooze, mute) via mutation calls. Badge counts synchronized via TanStack Query cache updates.

## 4. Conversational UI / Voice Integration
- **Message Timeline**: Virtualized list (React Virtuoso) showing agent/human avatars, persona tags, tool-call chips, streaming partial responses.
- **Voice Controls**: WebRTC capture, live waveform animations based on audio energy, caption overlays for accessibility. TTS playback uses AudioWorklet for low-latency streaming.
- **Audit Links**: Each message line exposes “View audit” to jump to logs, budgets, or capsule DAG nodes; deep links include `conversation_id` and timestamp.
- **Error Handling**: Inline toasts for constitution refusals, moderation blocks, tool failures; surfaces recommended next steps.

## 5. Accessibility & Theming
- WCAG 2.1 AA compliance: color contrast tokens, keyboard navigation, ARIA labeling for streaming elements.
- Tenant theming: design tokens stored per tenant (colors, logos, accent fonts), applied via CSS variables.
- Localization: i18n with react-intl; dynamic locale switching depending on user profile; ensures right-to-left support.

## 6. Deployment & Integration
- Build pipeline integrates with CI (linting via ESLint/Prettier, type checking via `tsc --noEmit`, Cypress/Playwright smoke tests).
- Static assets served via CDN with edge caching; invalidate on deploy; environment-specific env vars for API endpoints and feature flags.
- Observability: Front-end emits OpenTelemetry web traces with session IDs; errors captured via Sentry equivalent; UX metrics (TTFB, FID, Web Vitals) logged to analytics pipeline.

## 7. Next Steps
1. Finalize high-fidelity design system in Figma mirroring Tailwind/Radix tokens.
2. Scaffold Vite+React workspace under `apps/admin-console/` (seed project committed).
3. Implement notification orchestrator service (FastAPI) and WebSocket gateway; integrate with Kafka topic.
4. Build conversation timeline prototype with WebSocket streaming and voice waveform preview.
5. Wire notification preference CRUD endpoints in `settings-service` and corresponding UI forms.
6. Create Storybook for core components (buttons, modals, notification toast, message bubble, audio control).
7. Add Playwright smoke tests for login, notification tray, conversation stream, and settings update flows.

## 8. Detailed Interface Modules
### Benchmark Visualization
- Dedicated section within Operations Dashboard showing per-provider metrics (quality, latency, cost, refusal rate, audio WER/MOS) with trend lines and threshold alerts.
- Users can filter by deployment mode, model role, persona, or tenant opt-in.
- Includes badges highlighting models ready for promotion or requiring rollback based on benchmark results.
- Provides drill-down to raw benchmark logs stored in SomaBrain for audit.

### Admin Console
### Health & Metrics Overview
- **Agent One Sight** dashboard surfaces live KPIs: SomaBrain latency/uptime, SomaFractal Memory replication lag, Kafka backlog depth, active capsule count, policy violation rate, token burn vs forecast.
- **Status Indicators**: LED-style badges (green/amber/red) for core dependencies (SomaBrain, SLM providers, Redis, Kafka, Temporal); click to view incident runbooks.
- **Personalized Widgets**: Users can pin metrics (e.g., voice MOS, conversation latency, training sessions) and save layouts per tenant. Preferences stored in `dashboard_preferences` table via `settings-service`.
- **Anomaly Timeline**: Sparkline matrix showing last 24h error spikes, moderation strikes, token overruns. Drill-down opens observability dashboards.
- **Capsule Performance Heatmap**: Shows success/rollback rates by capsule type and persona; ties into benchmarking capsules.
- **Export & Alerts**: One-click export to CSV/PDF, subscribe to alert thresholds (e.g., SomaBrain latency > 500ms). Hooks into existing notification system.

- **Navigation**: Left rail with collapsible sections (Identity & Access, Models & Providers, Memory & SomaBrain, Tools & Integrations, Marketplace & Personas, Automation & Maintenance). Breadcrumbs reflect tenant scope.
- **Forms**: Use Radix Dialog + Form components, inline validation, optimistic updates with rollback on API failure. Secrets handled via masked inputs referencing Vault IDs.
- **Model Profile Editor**: Matrix view (roles vs deployment modes) showing primary/fallback models, latency/cost metrics, and toggle to promote staged versions.
- **Deployment Mode Switcher**: Wizard-style workflow verifying dependencies before applying mode change, with confirmation modals and audit preview.
- **Notification Preferences**: Per-user grid of channels (web, email, SMS, webhook) with severity sliders and quiet hours scheduler.

### Operations Dashboard
- **Overview Cards**: Capsule throughput, token spend heatmap, active alerts, moderation queue counts.
- **Capsule DAG Visualizer**: D3/ReactFlow component showing nodes, statuses, durations, budgets; click-through to artifacts and audit logs.
- **Budget Timeline**: Stacked area chart of forecast vs actual; supports drill-down by persona or capsule.
- **Moderation Inbox**: Table with filters (severity, source), bulk actions (approve/escalate), inline constitution references.

### Conversational Workspace
- **Layout**: Two-column — left conversation list (tenants/projects), center timeline, right context pane (capsule plan, memory snippets, tools used).
- **Composer**: Markdown support, slash-commands for tools, upload drag-and-drop (files chunked and sent to memory gateway).
- **Voice Controls**: Push-to-talk button, visual VU meter, crossfade playback; accessibility alternative via keyboard shortcuts.
- **Persona Switcher**: Dropdown to swap persona shot; shows token budget impact before confirming.

### Notification Center
- **Tray**: Slide-over panel with tabs (All, Action Required, Systems). Each item shows severity badge, source service, quick action buttons.
- **Digest Emails**: Daily summary templates built with MJML; links route back to console with deep links preserving filters.
- **Mobile Push/Webhooks**: Outgoing channel adapters triggered via notification orchestrator (configurable per tenant).

### Marketplace & Builders
- **Persona Gallery**: Grid/list view with filters (domain, tools, cost tier). Hover reveals core traits, token estimates, compliance status.
- **Capsule Builder**: Visual canvas (drag personas, tools, policies) with YAML preview and validation, plus simulation runner to estimate tokens/time.
- **Tool Adapter Catalog**: Line items showing auth requirements, scopes, sandbox policies; install flows integrate with secrets manager modals.

### Responsive & Theming
- Breakpoints: mobile (<640px) simplified nav, tablet two-column, desktop full layout.
- Tenants can upload logos, choose color palette; CSS variables update live.
- Dark mode toggled per user, persisted in preferences table.

### Analytics & Instrumentation
- Every major interaction emits UX telemetry events (`uix.events`) with anonymized session IDs, allowing funnel analysis (e.g., capsule install success, notification engagement).
- Performance budgets defined (TTI < 2s, chat latency < 150ms for text, < 400ms for audio playback). Alerts trigger when budgets breached.

## 9. Shared Component Library
- Component folders: `atoms` (buttons, inputs), `molecules` (cards, tool chips), `organisms` (capsule list, notification tray).
- Expose via dedicated package `@somagent/uix` consumed by admin console and future clients.
- Storybook documents props, variants, accessibility notes; Chromatic handles visual regression gating.

## 10. Roadmap Integration
- Phase 2: Ship baseline admin settings + text chat UI.
- Phase 3: Add voice controls, audio visualizations, notification orchestration.
- Phase 4+: Release capsule builder, marketplace, advanced dashboards, and mobile-friendly notification channels.
