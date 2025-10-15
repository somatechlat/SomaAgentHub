# Intelligent Memory System

**Semantic memory and context management for AI agents**

The Intelligent Memory System is SomaAgentHub's advanced memory architecture that enables agents to store, recall, and share information intelligently. Unlike simple databases, this system uses semantic understanding to find relevant context and maintain coherent conversations across long time periods.

---

## 🎯 What is Intelligent Memory?

The Intelligent Memory System provides:

- **Semantic Search** - Find information by meaning, not just keywords
- **Persistent Context** - Maintain conversation state across sessions  
- **Cross-Agent Sharing** - Allow multiple agents to access shared memories
- **Automatic Organization** - Intelligent categorization and relationship mapping
- **Privacy Controls** - User-specific and tenant-specific memory isolation

### How It Works
Instead of storing raw text, the system creates **semantic embeddings** that capture meaning. When agents need information, they search by context and relevance rather than exact matches.

**Example**: An agent searching for "budget constraints" would find memories about "financial limitations," "spending restrictions," and "cost considerations" even if those exact words weren't used.

---

## 🚀 Quick Start

### 1. Store Information in Memory

```bash
curl -X POST http://localhost:8004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "user123",
    "content": "The Q4 marketing campaign should focus on sustainability messaging, targeting millennials and Gen Z customers who prioritize environmental responsibility.",
    "memory_type": "project_context",
    "metadata": {
      "project": "Q4_marketing_campaign", 
      "department": "marketing",
      "priority": "high",
      "created_by": "sarah.johnson",
      "tags": ["sustainability", "marketing", "target-audience"]
    }
  }'
```

### 2. Recall Relevant Information

```bash
curl -X POST http://localhost:8004/v1/recall \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "query": "What are our marketing priorities for environmental messaging?",
    "user_id": "user123",
    "limit": 5,
    "similarity_threshold": 0.7,
    "filters": {
      "memory_type": ["project_context", "strategic_decisions"],
      "department": "marketing"
    }
  }'
```

**Response:**
```json
{
  "memories": [
    {
      "id": "mem_abc123",
      "content": "The Q4 marketing campaign should focus on sustainability messaging...",
      "similarity_score": 0.92,
      "metadata": {
        "project": "Q4_marketing_campaign",
        "created_at": "2024-01-10T14:30:00Z",
        "tags": ["sustainability", "marketing"]
      }
    }
  ],
  "query_embedding": [...],
  "search_stats": {
    "total_searched": 1247,
    "results_returned": 1,
    "search_time_ms": 45
  }
}
```

### 3. Use Memory in Agent Conversations

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Create a social media strategy for our sustainability campaign"
      }
    ],
    "memory_config": {
      "use_memory": true,
      "memory_context_limit": 10,
      "relevance_threshold": 0.75
    },
    "user_id": "user123"
  }'
```

The agent will automatically retrieve relevant memories and incorporate them into the response.

---

## 🛠️ Memory Types & Organization

### Memory Categories

| Type | Purpose | Retention | Access Pattern |
|------|---------|-----------|----------------|
| `conversation_history` | Chat and dialogue context | Session-based | Sequential access |
| `project_context` | Project-specific information | Project lifecycle | Contextual search |
| `user_preferences` | Personal settings and preferences | Persistent | User-specific |
| `factual_knowledge` | Facts and reference information | Long-term | Global search |
| `procedural_knowledge` | How-to instructions and processes | Long-term | Task-specific |
| `temporal_events` | Time-based events and schedules | Time-bounded | Temporal queries |

### Memory Hierarchies

```json
{
  "memory_structure": {
    "user_level": {
      "personal_memories": "Private to individual user",
      "shared_memories": "Accessible to user's team"
    },
    "tenant_level": {
      "organization_memories": "Company-wide knowledge",
      "department_memories": "Department-specific context"
    },
    "global_level": {
      "public_knowledge": "General reference information",
      "system_knowledge": "Platform operational context"
    }
  }
}
```

---

## 💡 Advanced Use Cases

### 1. Personal AI Assistant Memory

**Scenario**: An AI assistant that remembers user preferences, past conversations, and personal context.

```bash
# Store personal preferences
curl -X POST http://localhost:8004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "john.doe",
    "content": "John prefers morning meetings between 9-11 AM, dislikes calls during lunch (12-1 PM), works from home on Fridays, and has a standing 4 PM coffee break.",
    "memory_type": "user_preferences",
    "metadata": {
      "category": "scheduling_preferences",
      "importance": "high",
      "auto_apply": true
    }
  }'

# Store project context
curl -X POST http://localhost:8004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "john.doe", 
    "content": "Currently leading the mobile app redesign project. Team of 4 developers, deadline is March 15th. Main challenges are user authentication and offline sync functionality.",
    "memory_type": "project_context",
    "metadata": {
      "project_id": "mobile_app_v2",
      "role": "project_lead",
      "deadline": "2024-03-15"
    }
  }'

# Later, when scheduling a meeting
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Can you schedule a project review meeting for next week?"
      }
    ],
    "memory_config": {
      "use_memory": true,
      "memory_types": ["user_preferences", "project_context"]
    },
    "user_id": "john.doe"
  }'
```

### 2. Knowledge Base for Customer Support

**Scenario**: Building an intelligent knowledge base that learns from support interactions.

```bash
# Store solution knowledge
curl -X POST http://localhost:8004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "support_system",
    "content": "API rate limiting errors (HTTP 429) are usually caused by exceeding 1000 requests per minute. Solution: Implement exponential backoff retry logic with jitter. Alternative: Contact support to increase rate limits for enterprise customers.",
    "memory_type": "support_solution",
    "metadata": {
      "problem_category": "api_errors",
      "error_code": "HTTP_429", 
      "solution_effectiveness": 0.95,
      "applies_to": ["api_integration", "rate_limiting"],
      "difficulty": "intermediate"
    }
  }'

# Query for solutions
curl -X POST http://localhost:8004/v1/recall \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "query": "Customer is getting too many requests error from our API",
    "user_id": "support_system",
    "filters": {
      "memory_type": ["support_solution"],
      "problem_category": ["api_errors"]
    },
    "limit": 3,
    "similarity_threshold": 0.8
  }'
```

### 3. Team Knowledge Sharing

**Scenario**: Cross-team knowledge sharing where insights from one project benefit others.

```bash
# Engineering team stores architectural decision
curl -X POST http://localhost:8004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "engineering_team",
    "content": "For microservices communication, we chose gRPC over REST for internal services due to better performance (40% faster) and type safety. However, we keep REST APIs for external integrations for better compatibility.",
    "memory_type": "architectural_decision",
    "metadata": {
      "domain": "system_architecture",
      "decision_date": "2024-01-15",
      "impacts": ["performance", "maintainability", "developer_experience"],
      "stakeholders": ["backend_team", "platform_team"],
      "confidence": 0.9
    },
    "sharing_policy": {
      "teams": ["backend", "platform", "product"],
      "visibility": "internal"
    }
  }'

# Product team searches for architecture patterns
curl -X POST http://localhost:8004/v1/recall \
  -H "Content-Type: application/json" \  
  -H "Authorization: Bearer demo-token" \
  -d '{
    "query": "What communication protocols should we use between services?",
    "user_id": "product_team",
    "filters": {
      "memory_type": ["architectural_decision", "best_practice"],
      "domain": ["system_architecture", "api_design"]
    },
    "team_scope": ["backend", "platform", "product"]
  }'
```

---

## 🔧 API Reference

### Store Memory

**Endpoint**: `POST /v1/memories`

**Request Body**:
```json
{
  "user_id": "string",
  "content": "string",
  "memory_type": "string",
  "metadata": {
    "category": "string",
    "priority": "high|medium|low",
    "tags": ["string"],
    "expires_at": "2024-12-31T23:59:59Z"
  },
  "sharing_policy": {
    "visibility": "private|team|organization|public",
    "teams": ["string"],
    "users": ["string"]
  },
  "embedding_config": {
    "model": "text-embedding-ada-002",
    "chunk_size": 1000,
    "overlap": 100
  }
}
```

### Recall Information  

**Endpoint**: `POST /v1/recall`

**Request Body**:
```json
{
  "query": "string",
  "user_id": "string", 
  "limit": 10,
  "similarity_threshold": 0.7,
  "filters": {
    "memory_type": ["string"],
    "metadata": {},
    "date_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-12-31T23:59:59Z"
    }
  },
  "ranking": {
    "algorithm": "semantic|hybrid|temporal",
    "boost_factors": {
      "recency": 0.1,
      "relevance": 0.8, 
      "importance": 0.1
    }
  }
}
```

### Memory Analytics

**Endpoint**: `GET /v1/memories/analytics`

**Query Parameters**:
- `user_id`: Filter by user
- `period`: Time period (day, week, month)
- `memory_types`: Comma-separated memory types

**Response**:
```json
{
  "usage_stats": {
    "total_memories": 1247,
    "memories_created_today": 23,
    "average_recall_frequency": 4.2,
    "top_memory_types": ["project_context", "user_preferences"]
  },
  "search_analytics": {
    "total_searches": 589,
    "average_response_time_ms": 45,
    "hit_rate": 0.87,
    "top_queries": ["project status", "team preferences", "api documentation"]
  },
  "memory_health": {
    "duplicate_detection": {
      "potential_duplicates": 12,
      "confidence_threshold": 0.95
    },
    "outdated_memories": 8,
    "orphaned_memories": 3
  }
}
```

---

## 🎛️ Advanced Configuration

### Embedding Models

```json
{
  "embedding_models": [
    {
      "name": "text-embedding-ada-002",
      "provider": "openai",
      "dimensions": 1536,
      "cost_per_token": 0.0001,
      "use_cases": ["general_purpose", "multilingual"]
    },
    {
      "name": "sentence-transformers/all-MiniLM-L6-v2",
      "provider": "local",
      "dimensions": 384,
      "cost_per_token": 0,
      "use_cases": ["fast_inference", "privacy_focused"]
    }
  ]
}
```

### Memory Lifecycle Management

```json
{
  "lifecycle_policies": [
    {
      "name": "conversation_cleanup",
      "applies_to": "conversation_history", 
      "rules": [
        {
          "condition": "age > 30 days AND importance < 0.3",
          "action": "archive"
        },
        {
          "condition": "age > 90 days",
          "action": "delete"
        }
      ]
    },
    {
      "name": "project_archival",
      "applies_to": "project_context",
      "rules": [
        {
          "condition": "project_status = completed AND age > 6 months",
          "action": "compress_and_summarize"
        }
      ]
    }
  ]
}
```

### Privacy and Security

```json
{
  "privacy_settings": {
    "encryption": {
      "at_rest": "AES-256-GCM",
      "in_transit": "TLS 1.3",
      "key_rotation": "90 days"
    },
    "access_controls": {
      "rbac_enabled": true,
      "audit_logging": true,
      "data_residency": "us-west-2"
    },
    "compliance": {
      "gdpr_enabled": true,
      "right_to_be_forgotten": true,
      "data_export": "json|xml"
    }
  }
}
```

---

## ❓ Troubleshooting

### Common Issues

**1. Memory Not Found**
```bash
# Check if memory was stored correctly
curl http://localhost:8004/v1/memories/MEMORY_ID

# Verify user permissions
curl http://localhost:8004/v1/memories?user_id=USER_ID&limit=10
```

**2. Poor Search Results**
```bash
# Check embedding quality
curl -X POST http://localhost:8004/v1/debug/similarity \
  -d '{"text1": "your query", "text2": "expected result"}'

# Adjust similarity threshold
curl -X POST http://localhost:8004/v1/recall \
  -d '{"query": "...", "similarity_threshold": 0.6}'
```

**3. Memory System Performance**
```bash
# Check vector database health
curl http://localhost:8004/v1/health/detailed

# Monitor search performance
curl http://localhost:8004/v1/metrics | grep search_duration
```

### Best Practices

1. **Meaningful Content** - Store substantial, contextual information rather than fragments
2. **Good Metadata** - Use rich metadata for better filtering and organization
3. **Regular Cleanup** - Implement lifecycle policies to manage memory growth
4. **Monitor Usage** - Track search patterns and memory effectiveness
5. **Privacy Awareness** - Be mindful of sensitive information storage and access

---

## 🔗 Related Features

- **[Session Management](session-management.md)** - Persistent conversations using memory
- **[Multi-Agent Orchestration](multi-agent-orchestration.md)** - Shared memory between agents  
- **[API Gateway](api-gateway.md)** - Memory-enhanced chat completions
- **[Policy & Governance](policy-governance.md)** - Memory access controls

---

**Intelligent Memory transforms static AI agents into learning systems that grow smarter over time. Ready to build memory-enabled agents?**
