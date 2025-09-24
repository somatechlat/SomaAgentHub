# SomaGent SLM Strategy

This note outlines how SomaGent selects, operates, and administrates small language models (SLMs) across the platform. It complements the architecture and roadmap documents by detailing role-specific model assignments, scoring math, and configuration flows.

## 1. Role-Based Model Personas

SomaGent separates model usage into functional roles. Each role can have a primary model and one or more fallbacks.

| Role | Responsibilities | Primary Example | Backup / Notes |
|------|------------------|-----------------|----------------|
| Dialogue & Reasoning | Orchestrator conversations, capsule planning, constitutional explanations. | `gpt-4o-mini` or `claude-3-5-sonnet` | `mistral-large` self-host option for air-gapped tenants. |
| Tool Call Planning | Decide next action, clarify policy results, lightweight intent routing. | `gpt-4o-mini` (low temperature) | `llama-3-8b-instruct` for on-prem speed. |
| Code / Structured Output | Generate code, configs, Terraform, YAML, tests. | `gpt-4o` or `claude-3-5-haiku` | `codestral-latest` for OSS requirements. |
| Knowledge Ops | Embeddings, semantic search, capsule retrieval. | `text-embedding-3-large` | `voyage-multilingual-2` or self-hosted BGE. |
| Summaries & Reports | Capsule retros, PM updates, audit digests. | `claude-3-5-haiku` | `gpt-4o-mini` reuse for low latency. |
| Speech Recognition | Low-latency transcription for voice conversations, timestamps, diarization. | `whisper-large-v3` or `deepgram-nova-2` | On-prem `vosk` / `nemo` for air-gapped tenants. |
| Speech Synthesis | Natural, expressive text-to-speech for agent replies. | `elevenlabs-conversational-v2` or Azure Neural Voices | OSS fallback via `bark-large` or `kokoro`. |

Key principles:
- Each role has explicit constitutional guard-rails and temperature defaults.
- Deployment mode (developer, test, production) can override the primary/backup combination.
- Observability tags every request with its role so telemetry stays comparable.

## 2. Model Scoring Math

To decide which model backs a role, SomaGent computes a composite score using observed metrics:

```
score(model, task) = w_q * quality(model, task)
                   + w_c * (1 / cost(model))
                   + w_l * (1 / latency(model))
                   + w_r * reliability(model)
```

- `quality` – capsule-specific evaluation (e.g., diff accuracy for code, summarization faithfulness). Stored from regression capsules and production telemetry.
- `cost` – effective tokens or currency per request. Pulled from billing logs.
- `latency` – p95 or p99 duration for the role.
- `reliability` – refusal accuracy, provider uptime, policy-compliant responses.
- Weights (`w_q`, `w_c`, `w_l`, `w_r`) differ per deployment mode (production prioritizes quality/reliability; developer modes weigh latency/cost higher).

The scoring service:
1. Persists per-model metrics (`slm.metrics` topic → Postgres).
2. Recalculates scores nightly (or on demand) per role and deployment mode.
3. Emits `model.profile.scored` events for audit.

## 3. Configuration & Administration

- **Model Profiles**: Settings service stores profiles (`chat`, `planning`, `code`, `summary`, `embedding`). Each profile contains primary model, fallbacks, temperature, max_tokens, and provider credentials reference.
- **Deployment Integration**: `SOMAGENT_DEPLOYMENT_MODE` picks default profiles (e.g., `developer-light` → OSS/default; `production` → managed providers). Mode changes publish `mode.changed` events so SLM workers reload configs.
- **Tenant Overrides**: Admin console lets tenants choose different models per profile if they provide keys and accept budget impacts. Updates trigger `model.profile.updated` events.
- **Version Upgrades**: New model versions run through regression capsules in `test` mode. If quality improves and score increases above threshold, admins can promote the version in UI or API. Promotion writes to Postgres and notifies all SLM workers.
- **Fallback Logic**: SLM service tracks provider health. On high latency or errors, it automatically switches to fallback models according to profile order and emits `model.fallback.used` telemetry.

## 4. Operational Flow

1. Orchestrator tags each SLM request with `role` metadata.
2. SLM gateway consults active profile for the role and deployment mode.
3. Request executes against primary model; response metrics (tokens, duration, outcome) are logged.
4. Token estimator consumes metrics to update `baseline`, `tool_coeff`, and `persona_factor` terms.
5. Nightly scoring job recomputes `score` per model and may recommend profile changes.

## 5. Audio Conversation Pipeline

### Audio Vector & Energy Modeling
- **Feature Extraction**: Incoming audio chunks are converted into log-mel spectrograms and MFCC vectors; we retain time-aligned energy envelopes to capture emphasis and pauses.
- **Vector Persistence**: Embeddings are stored per tenant in SomaBrain/Quadrant with tags (`conversation_id`, `persona_id`) to enable similarity search, replay, and anomaly detection without persisting raw waveforms.
- **Energy Analytics**: Calculate RMS energy, zero-crossing rate, and spectral entropy per segment to detect excitement, whispering, or anomalies; expose aggregates to the policy engine for escalation rules.
- **Quality Metrics**: Word error rate (WER), character error rate (CER), MOS-LQO estimates, and token/energy alignment feed the scoring function so model selection stays math-driven.
- **Governance**: Audio vectors are encrypted in transit and at rest; access requires `conversation:inspect` capability, and audit logs only record hashes plus derived metrics (never raw audio).


- **Capture**: Conversational Experience Service accepts WebRTC/WebSocket audio streams, runs voice activity detection, and submits buffered chunks to the ASR profile (`speech_recognition`).
- **Transcribe**: ASR adapters return text with timestamps + confidence; the service normalizes into intent events and forwards to the orchestrator with speaker metadata.
- **Respond**: Orchestrator / SLM dialogue role generates text; Conversational Experience Service optionally rewrites for persona tone and streams partial tokens back to the client.
- **Synthesize**: Response segments feed the TTS profile (`speech_synthesis`), generating PCM/Opus audio blocks for immediate playback; fallback to text if synthesis fails.
- **Audit & Metrics**: Each stage logs latency, quality scores (word error rate, MOS), and moderation signals to `conversation.events`, ensuring math-driven tuning for audio models.


## 6. Benchmark Methodology

- **Benchmarks**: Nightly capsules covering translation, long-form reasoning, tool calling, code generation, summarization, question answering, audio transcription, and speech synthesis. Each capsule replays the same prompts, tools, and expected outputs per provider.
- **Metrics**: For text LLMs collect quality scores (BLEU, ROUGE, factual accuracy checks, hallucination rate), latency (p50/p95), cost per 1K tokens, refusal rate, policy violation incidents. For code tasks run unit tests/linters. For audio capture WER, CER, MOS-LQO, streaming latency.
- **Data Sets**: Combine public benchmarks (e.g., MMLU subsections, BigBench Lite) with SomaGent-specific corpora (capsule scripts, customer anonymized tasks). Store inputs/expected results versioned in SomaBrain to ensure reproducibility.
- **Automation**: Temporal workflow (`benchmark.orchestrator`) triggers runs per deployment mode, publishes results to `slm.benchmark.results`, and writes summary tables for the scoring service. Failures send notifications.
- **Promotion Gates**: A new model version must meet or exceed thresholds (quality + latency + refusal compliance) and pass manual review before being promoted to production profiles. Staging profiles let admins test before rollout.
- **Reporting**: Admin dashboard shows trend charts for each provider/model, including drift detection. Reports exportable (CSV/PDF) for compliance teams.
- **Continuous Improvement**: Logs feed back to the token estimator, tool adapter heuristics, and persona prompts. Regression detection automatically opens work items when a metric regresses beyond tolerance.

## 6. Next Implementation Steps

- Define `model_profiles` schema in settings service and expose CRUD API.
- Extend SLM HTTP surface (`/infer_sync`, `/embedding`) to accept `role` and use the configured profile.
- Build scoring job (batch or streaming) that reads telemetry, updates per-model metrics, and emits ranking suggestions.
- Implement ASR/TTS adapters with streaming codecs (Opus/PCM) and connect them to the Conversational Experience Service.
- Add conversational dashboards that surface WER, MOS, and latency so admins can tune audio providers.
- Integrate admin console UI for selecting models, viewing scores, and scheduling upgrades.
- Document deployment-mode defaults in configuration (developer vs production).

This structure keeps SLM usage elegant, observable, and easy to tune while remaining math-driven and simple to reason about.
