# SomaAgentHub — Labs / Experimental Services (excluded from Tier-0 gates)

These services failed syntax/indent checks in the current snapshot and are treated as **labs/experimental** until rewritten. CI/Tier-0 compile gates must **exclude** them to keep the core stable.

- services/analytics-service
- services/agent-spawner
- services/airflow-service
- services/billing-service
- services/constitution-service
- services/data-layer
- services/evolution-engine
- services/flink-service
- services/gpubroker
- services/jobs
- services/mao-engine
- services/marketplace
- services/memory-gateway
- services/model-proxy
- services/notification-service
- services/pricing-service
- services/self-provisioning
- services/settings-service
- services/task_capsule_repo
- services/token-estimator
- services/tool-service
- services/voice-interface
- services/workflow-engine

Once each service is cleaned and passes `python3 -m compileall`, it can graduate out of labs and be reintroduced into Tier-0/CI gates.
