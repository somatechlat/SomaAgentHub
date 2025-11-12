# SomaAgentHub Examples

This directory contains runnable demonstrations that exercise different parts of the SomaAgentHub platform. Each example includes lightweight test data so you can validate a real stack without mock responses.

## Marketing Campaign Wizard (`marketing_campaign_wizard.py`)

- **Purpose**: Walk through the `marketing_campaign_v1` wizard exposed by the Gateway API and verify end-to-end plan synthesis.
- **Prerequisites**: Gateway API running locally (`make dev-start-services`), Orchestrator + Temporal (`make dev-up orchestrator` or docker-compose stack), Python 3.11+, `requests` (already in repo requirements).
- **Usage**:
  ```bash
  source .venv/bin/activate
  python examples/marketing_campaign_wizard.py --approve --poll-orchestrator --plan-output plans/marketing-plan.json
  ```
- **Real orchestration**: Ensure the Orchestrator service and Temporal backend are running (`make dev-up orchestrator` or your deployment pipeline) and export `SOMA_AGENT_HUB_GATEWAY_ORCHESTRATOR_URL=http://localhost:10001` so the Gateway can reach it.
- **Test Data**:
  - Campaign name: `Fall 2025 AI Platform Launch`
  - Campaign type: `product_launch`
  - Target audience: `Enterprise CTOs, DevOps Engineers, AI/ML Teams`
  - Channels: `["email", "blog", "social_linkedin", "social_twitter"]`
  - Launch date: `2025-10-21`
  - Budget: `10000`
  - Key messages: `Revolutionary AI agent platform. 10x faster deployment. Enterprise-grade security. Open-source foundation.`
  - Success metrics: `["impressions", "clicks", "leads", "signups", "engagement"]`
  - Brand voice: `professional`
- **Expected Outcome**: The script lists available wizards, answers each question with the provided dataset (or interactive input), writes the rendered execution plan, and—when `--approve` is set—triggers the Multi-Agent Orchestrator and optionally polls workflow status via Temporal.

> Looking for the original cURL walkthrough? `wizard-demo.sh` remains available for quick inspection of the HTTP surface.

### Monitor Orchestrations (`monitor_mao_workflow.py`)

- **Purpose**: Poll a MAO workflow by ID until it reaches a terminal state.
- **Usage**:
  ```bash
  source .venv/bin/activate
  python examples/monitor_mao_workflow.py mao-mao-<workflow-id> --show-history-length
  ```
- Combine with the marketing wizard CLI by copying the `workflow_id` from the approval response.

## Additional Examples

Refer to the inline docstrings at the top of each script/app for their specific scenarios and required inputs:

- `accounting_software_demo.py` – requirement intake for a finance software build.
- `agent_call_example.py` – Python SDK call path for health checks and conversations.
- `chatbot/`, `code-assistant/`, `data-analysis/` – Rich terminal apps showcasing specialized agents.
- `kamachiq-demo/`, `mao-project/` – Full multi-agent orchestration and autonomous project workflows.
