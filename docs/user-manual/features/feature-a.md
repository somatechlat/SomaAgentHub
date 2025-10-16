# Multi-Agent Orchestration

**Coordinate multiple AI agents in complex, intelligent workflows**

Multi-Agent Orchestration is SomaAgentHub's flagship feature that enables you to coordinate multiple specialized AI agents working together on complex tasks. Unlike single-agent systems, this allows for parallel processing, specialized expertise, and sophisticated workflow coordination.

---

## 🎯 What is Multi-Agent Orchestration?

Multi-Agent Orchestration allows you to:

- **Coordinate Multiple Agents** - Have different agents handle different aspects of a task
- **Parallel Processing** - Run multiple agents simultaneously for faster completion
- **Specialized Expertise** - Use agents optimized for specific domains (research, analysis, writing, etc.)
- **Fault Tolerance** - Continue workflows even if individual agents fail
- **State Management** - Maintain context and progress across all agents

### Real-World Example
Instead of asking one AI to "research, analyze, and write a report," you orchestrate:
- **Research Agent** - Gathers information from multiple sources
- **Analysis Agent** - Processes data and identifies patterns  
- **Writing Agent** - Creates well-structured reports
- **Review Agent** - Ensures quality and accuracy

---

## 🚀 Quick Start

### 1. Basic Multi-Agent Workflow

```bash
curl -X POST http://localhost:10001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "multi_agent_research",
    "input": {
      "topic": "Sustainable Energy Trends 2024",
      "agents": [
        {"role": "researcher", "expertise": "energy_policy"},
        {"role": "analyst", "expertise": "market_trends"},  
        {"role": "writer", "expertise": "technical_writing"}
      ],
      "coordination": "sequential_with_review"
    },
    "metadata": {
      "user_id": "your-user-id",
      "priority": "high"
    }
  }'
```

### 2. Monitor Agent Coordination

```bash
# Replace WORKFLOW_ID with your actual workflow ID
curl http://localhost:10001/v1/workflows/WORKFLOW_ID \
  -H "Authorization: Bearer demo-token"
```

**Response shows agent coordination:**
```json
{
  "run_id": "wf_multi_abc123",
  "status": "running",
  "agents": [
    {
      "agent_id": "researcher-001",
      "role": "researcher",
      "status": "completed",
      "output_summary": "Gathered 45 sources on renewable energy policies"
    },
    {
      "agent_id": "analyst-001", 
      "role": "analyst",
      "status": "active",
      "current_task": "Analyzing policy impact on market adoption"
    },
    {
      "agent_id": "writer-001",
      "role": "writer", 
      "status": "waiting",
      "waiting_for": "analyst-001 completion"
    }
  ]
}
```

---

## 🛠️ Configuration Options

### Workflow Types

| Workflow Type | Description | Use Cases |
|---------------|-------------|-----------|
| `multi_agent_research` | Research with multiple specialized agents | Academic research, market analysis |
| `collaborative_writing` | Multiple agents writing different sections | Documentation, reports, content creation |
| `data_processing_pipeline` | Sequential data transformation | ETL processes, data analysis |
| `approval_workflow` | Human-in-the-loop with agent assistance | Document review, decision making |
| `competitive_analysis` | Multiple agents analyzing different competitors | Business intelligence, market research |

### Coordination Patterns

```json
{
  "coordination": "parallel",           // All agents work simultaneously
  "coordination": "sequential",         // Agents work one after another
  "coordination": "sequential_with_review", // Each step reviewed before next
  "coordination": "hierarchical",       // Supervisor agent coordinates others
  "coordination": "event_driven"        // Agents react to specific events
}
```

### Agent Specialization

```json
{
  "agents": [
    {
      "role": "researcher",
      "expertise": "academic_papers",
      "tools": ["web_search", "arxiv_api", "pubmed"],
      "constraints": {
        "max_sources": 50,
        "quality_threshold": 0.8
      }
    },
    {
      "role": "analyst", 
      "expertise": "statistical_analysis",
      "tools": ["python_executor", "data_visualization"],
      "requirements": {
        "input_from": ["researcher"],
        "output_format": "structured_analysis"
      }
    }
  ]
}
```

---

## 💡 Advanced Use Cases

### 1. Customer Support Resolution

**Scenario**: Multi-agent customer support that handles complex technical issues.

```bash
curl -X POST http://localhost:10001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "customer_support_resolution",
    "input": {
      "issue": {
        "id": "TICKET-12345",
        "category": "technical",
        "description": "API authentication failing intermittently",
        "customer_tier": "enterprise"
      },
      "agents": [
        {
          "role": "triage_agent",
          "expertise": "issue_classification",
          "tools": ["ticket_system", "knowledge_base"]
        },
        {
          "role": "technical_agent", 
          "expertise": "api_debugging",
          "tools": ["log_analyzer", "system_monitor"]
        },
        {
          "role": "communication_agent",
          "expertise": "customer_communication", 
          "tools": ["email", "slack"]
        }
      ],
      "escalation_rules": {
        "auto_escalate_after": "2 hours",
        "escalate_to": "senior_engineer"
      }
    }
  }'
```

### 2. Content Creation Pipeline

**Scenario**: Multi-agent content creation for blog posts, documentation, and marketing materials.

```bash
curl -X POST http://localhost:10001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "content_creation_pipeline",
    "input": {
      "content_brief": {
        "topic": "AI Ethics in Enterprise Applications",
        "target_audience": "CTOs and technical leaders",
        "content_types": ["blog_post", "whitepaper", "social_posts"]
      },
      "agents": [
        {
          "role": "research_agent",
          "expertise": "ai_ethics_research",
          "tools": ["academic_search", "news_aggregator"]
        },
        {
          "role": "outline_agent",
          "expertise": "content_structure",
          "input_dependencies": ["research_agent"]
        },
        {
          "role": "writer_agent",
          "expertise": "technical_writing",
          "input_dependencies": ["outline_agent"]
        },
        {
          "role": "editor_agent",
          "expertise": "copy_editing",
          "input_dependencies": ["writer_agent"]
        },
        {
          "role": "seo_agent",
          "expertise": "search_optimization",
          "input_dependencies": ["editor_agent"]
        }
      ]
    }
  }'
```

### 3. Data Science Project Automation

**Scenario**: End-to-end data science project with multiple specialized agents.

```bash
curl -X POST http://localhost:10001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "data_science_project",
    "input": {
      "project": {
        "name": "Customer Churn Prediction",
        "data_source": "s3://company-data/customer-data.csv",
        "objective": "binary_classification",
        "success_metric": "f1_score > 0.85"
      },
      "agents": [
        {
          "role": "data_explorer",
          "expertise": "exploratory_data_analysis",
          "tools": ["pandas", "matplotlib", "seaborn"]
        },
        {
          "role": "feature_engineer", 
          "expertise": "feature_engineering",
          "tools": ["scikit_learn", "feature_tools"],
          "input_dependencies": ["data_explorer"]
        },
        {
          "role": "model_trainer",
          "expertise": "machine_learning",
          "tools": ["xgboost", "lightgbm", "pytorch"],
          "input_dependencies": ["feature_engineer"]
        },
        {
          "role": "model_evaluator",
          "expertise": "model_validation", 
          "tools": ["mlflow", "wandb"],
          "input_dependencies": ["model_trainer"]
        }
      ]
    }
  }'
```

---

## 🔧 API Reference

### Start Multi-Agent Workflow

**Endpoint**: `POST /v1/workflows/start`

**Request Body**:
```json
{
  "workflow_type": "string",
  "input": {
    "agents": [
      {
        "role": "string",
        "expertise": "string", 
        "tools": ["string"],
        "constraints": {},
        "input_dependencies": ["string"]
      }
    ],
    "coordination": "string",
    "timeout": "duration",
    "retry_policy": {}
  },
  "metadata": {
    "user_id": "string",
    "priority": "string"
  }
}
```

### Monitor Agent Status

**Endpoint**: `GET /v1/workflows/{workflow_id}/agents`

**Response**:
```json
{
  "agents": [
    {
      "agent_id": "string",
      "role": "string", 
      "status": "waiting|active|completed|failed",
      "progress": {
        "current_task": "string",
        "completion_percentage": 0.75,
        "estimated_completion": "2024-01-15T14:30:00Z"
      },
      "output": {
        "summary": "string",
        "artifacts": ["string"],
        "next_agent_input": {}
      },
      "metrics": {
        "execution_time": "5m30s",
        "tokens_used": 2500,
        "api_calls": 12
      }
    }
  ]
}
```

### Agent Communication

**Endpoint**: `POST /v1/workflows/{workflow_id}/agents/{agent_id}/message`

```json
{
  "message": {
    "type": "instruction|data|feedback",
    "content": "string",
    "metadata": {}
  },
  "target_agents": ["string"]
}
```

---

## 🎛️ Advanced Configuration

### Custom Agent Definitions

```json
{
  "custom_agents": [
    {
      "name": "legal_reviewer",
      "description": "Specialized agent for legal document review",
      "system_prompt": "You are a legal expert specializing in contract review...",
      "tools": ["legal_database", "compliance_checker"],
      "constraints": {
        "confidentiality": "high",
        "output_format": "structured_legal_analysis"
      },
      "capabilities": [
        "contract_analysis",
        "risk_assessment", 
        "compliance_checking"
      ]
    }
  ]
}
```

### Workflow Templates

```json
{
  "templates": [
    {
      "name": "market_research_template",
      "description": "Standard market research workflow",
      "agents": [
        {"role": "primary_researcher", "expertise": "market_analysis"},
        {"role": "competitor_analyst", "expertise": "competitive_intelligence"},
        {"role": "trend_analyst", "expertise": "trend_identification"},
        {"role": "report_writer", "expertise": "business_writing"}
      ],
      "coordination": "sequential_with_parallel_branches",
      "estimated_duration": "2-4 hours",
      "output_format": "comprehensive_market_report"
    }
  ]
}
```

---

## ❓ Troubleshooting

### Common Issues

**1. Agents Not Communicating**
```bash
# Check agent status
curl http://localhost:10001/v1/workflows/WORKFLOW_ID/agents

# Verify message passing
curl http://localhost:10001/v1/workflows/WORKFLOW_ID/messages
```

**2. Workflow Stuck in Waiting State**
```bash
# Check dependencies
curl http://localhost:10001/v1/workflows/WORKFLOW_ID/dependencies

# Manual agent trigger (if needed)
curl -X POST http://localhost:10001/v1/workflows/WORKFLOW_ID/agents/AGENT_ID/trigger
```

**3. Agent Performance Issues**
```bash
# Check agent metrics
curl http://localhost:10001/v1/workflows/WORKFLOW_ID/agents/AGENT_ID/metrics

# Review execution logs
curl http://localhost:10001/v1/workflows/WORKFLOW_ID/logs
```

### Best Practices

1. **Start Small** - Begin with 2-3 agents before scaling up
2. **Clear Roles** - Define distinct responsibilities for each agent
3. **Handle Dependencies** - Clearly specify input/output relationships
4. **Monitor Progress** - Use the monitoring APIs to track coordination
5. **Plan for Failures** - Include retry logic and fallback strategies

---

## 🔗 Related Features

- **[Workflow Management](workflow-management.md)** - Understanding workflow execution
- **[Intelligent Memory](intelligent-memory.md)** - Sharing context between agents
- **[Policy & Governance](policy-governance.md)** - Ensuring agent compliance
- **[Tool Integration](tool-integration.md)** - Connecting agents to external services

---

**Multi-Agent Orchestration transforms complex tasks into coordinated, intelligent workflows. Ready to orchestrate your first multi-agent system?**
