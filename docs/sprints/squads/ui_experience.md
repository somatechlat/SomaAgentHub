⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Squad Charter — UI & Experience

## Mission
Deliver the admin console, conversation workspace, and notification surfaces that showcase real backend capabilities with zero mocks and production-grade telemetry.

## Wave Alignment
- **Wave B (Weeks 2–3)** — Consumes Wave A backend outputs to ship live experiences.
- **Design Wave (Weeks 1–2)** — Stays one sprint ahead by publishing component specs and flows in `docs/design/`.

## Wave B Deliverables
- [ ] Publish Figma snapshots + API contracts in `docs/design/wave-2/ui/` covering admin settings, conversation timeline, notification tray.
- [ ] Implement admin console settings forms wired to live `/v1/settings` APIs with optimistic updates backed by real responses.
- [ ] Ship conversation workspace streaming via Gateway SSE using live `slm.responses` events (no mocks).
- [ ] Launch notification center integrating WebSocket feed from notification orchestrator.

### Dependencies
- Gateway SSE + policy headers delivered by Policy & Orchestration squad.
- Settings and identity endpoints stable at start of Wave B.
- Analytics dashboards from Infra to display metrics inside UI.

## Design Wave Preparations (Ready before Wave B Start)
- [ ] Component library stories updated in `apps/admin-console/storybook` with live data captures.
- [ ] Recorded API interactions using `scripts/parallel/record_contracts.py` stored under `docs/design/contracts/<date>/`.
- [ ] Accessibility criteria documented for each feature.

## Telemetry & Quality Gates
- Frontend metrics captured via web vitals export to analytics-service.
- Playwright regression suites run nightly hitting live staging.
- No feature closes without `docs/Quickstart.md` snippet demonstrating UI workflow end-to-end.

## Risks & Mitigations
- **Risk:** Backend API drift → Mitigate by consuming recorded contracts and attending twice-weekly design clinic.
- **Risk:** WebSocket scaling issues → Mitigate with load test harness coordinated with Infra squad.
