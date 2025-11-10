# VIBE CODING RULES (Canonical)

These rules govern all development in this repository. They are mandatory.

## 1. Core Principles
1. No Bullshit: No lies, no mocks, no placeholders, no fake implementations.
2. Check First, Code Second: Inspect existing files & architecture before adding/changing.
3. No Unnecessary Files: Prefer modifying existing code; justify any new file.
4. Real Implementations Only: No TODO stubs; either implement fully or explicitly defer with reason.
5. Documentation = Truth: Read real docs; never invent APIs; cite sources when relevant.
6. Complete Context Required: Understand data flow and dependencies before edits.
7. Real Data/Servers: Integrate with actual services; avoid assumptions.

## 2. Workflow Steps (Every Task)
1. Understand → parse request; ask concise clarifying questions if needed.
2. Gather Knowledge → read docs, config, code, schemas.
3. Investigate → trace flows, upstream/downstream impacts.
4. Verify Context → confirm full understanding or request missing pieces.
5. Plan → list affected files, changes, rationale, risks.
6. Implement → production-ready code, error handling, no placeholders.
7. Verify → edge cases, limitations, honesty about status; align with rules above.

## 3. Communication Style
Straight, concise, realistic. No hype adjectives. State facts and limitations.

## 4. Never Do
Invent undocumented APIs, create gratuitous files, leave half-finished code, gloss over uncertainty, assume library behavior.

## 5. Always Do
Reference existing code, reuse patterns, keep changes minimal & surgical, enforce UTC, typed models, clear error handling, instrumentation where appropriate.

## 6. Security & Integrity Additions
Use mTLS/service auth for internal calls; verify external data; record provenance for pricing snapshots; never log secrets.

## 7. Observability Expectations
Expose metrics for key operations; include trace correlation IDs; log structured JSON (no prints).

## 8. Deviation Protocol
If a rule cannot be followed (e.g., external doc unavailable), explicitly state deviation, reason, and mitigation.

## 9. Enforcement
PRs or changes lacking adherence may be rejected; roadmap banner mandates review.

---
This file is referenced at the top of `docs/ROADMAP.md` and must remain stable. Update only to refine clarity or add substantiated practices.
