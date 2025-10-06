# Planner Prompt Templates

Store prompt templates for planner requests here. Each template should capture:

- Capsule blueprint identifier(s)
- Required context variables (e.g., tenant defaults, tool availability summary)
- Output contract summary (keys that must appear in the LLM response)

Templates will be loaded by ``planner_service.py`` once the LLM integration is completed.
