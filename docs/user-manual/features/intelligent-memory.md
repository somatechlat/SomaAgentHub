# Intelligent Memory

**Persistent context and knowledge management for AI agents**

> SomaAgentHub's Intelligent Memory system provides vector storage, semantic search, and context recall capabilities that enable agents to maintain long-term memory across sessions and workflows.

---

## 📋 Overview

Intelligent Memory is SomaAgentHub's advanced memory management system that allows AI agents to:

- **Store and Retrieve Context** - Maintain conversation history and workflow state
- **Semantic Search** - Find relevant information using vector similarity
- **Cross-Session Memory** - Recall information from previous interactions
- **Knowledge Base Integration** - Access organizational knowledge and documentation
- **Memory Optimization** - Automatically manage memory usage and relevance

---

## 🧠 Core Capabilities

### Vector Storage
Store and search unstructured data using semantic embeddings:

```python
# Store document in memory
memory_client.store_document(
    content="SomaAgentHub deployment requires Kubernetes 1.24+",
    metadata={"type": "deployment", "category": "requirements"},
    tags=["kubernetes", "deployment", "infrastructure"]
)

# Semantic search
results = memory_client.search(
    query="What are the Kubernetes requirements?",
    limit=5,
    filters={"category": "requirements"}
)
```

### Context Management
Maintain agent context across sessions:

```python
# Store agent context
context = {
    "user_preferences": {"language": "python", "framework": "fastapi"},
    "current_project": "microservices-refactor",
    "conversation_history": [...],
    "workflow_state": {"step": 3, "completed_tasks": [...]}
}

memory_client.store_context(
    agent_id="agent-123",
    session_id="session-456",
    context=context
)

# Retrieve context in new session
restored_context = memory_client.get_context(
    agent_id="agent-123",
    session_id="session-789"  # New session
)
```

### Knowledge Base Integration
Connect to organizational knowledge sources:

```python
# Index documentation
memory_client.index_knowledge_base(
    source="confluence",
    documents=confluence_docs,
    metadata={"source": "internal_docs", "department": "engineering"}
)

# Query knowledge base
knowledge = memory_client.query_knowledge(
    question="How do we handle database migrations?",
    sources=["confluence", "github_wiki"],
    context="deployment_procedures"
)
```

---

## 🚀 Getting Started

### 1. Enable Memory Gateway

**In Web Interface:**
1. Navigate to **Settings** → **Memory Configuration**
2. Enable **Intelligent Memory**
3. Configure **Vector Database** connection (Qdrant)
4. Set **Memory Retention** policies

**Via CLI:**
```bash
# Enable memory gateway
soma config set memory.enabled true
soma config set memory.backend qdrant
soma config set memory.retention_days 90

# Verify configuration
soma memory status
```

### 2. Configure Memory Policies

**Memory Retention:**
```yaml
# memory-config.yaml
retention_policies:
  conversation_history: 30d
  workflow_context: 90d
  knowledge_base: 1y
  temporary_context: 7d

storage_limits:
  max_documents_per_agent: 10000
  max_context_size_mb: 100
  max_search_results: 50
```

**Privacy Settings:**
```yaml
privacy_settings:
  encrypt_at_rest: true
  anonymize_pii: true
  data_classification:
    - public
    - internal
    - confidential
  retention_overrides:
    confidential: 30d
    public: 1y
```

### 3. Agent Memory Integration

**Enable Memory for Agent:**
```python
from somaagent import Agent, MemoryConfig

agent = Agent(
    name="research-assistant",
    memory_config=MemoryConfig(
        enabled=True,
        context_window=4000,
        semantic_search=True,
        auto_summarization=True
    )
)

# Agent automatically uses memory
response = agent.process(
    "What did we discuss about the API design yesterday?"
)
```

---

## 💡 Use Cases

### Long-Running Projects
Maintain context across extended development cycles:

**Scenario**: Multi-week software development project
- **Context Storage**: Requirements, decisions, progress updates
- **Knowledge Retrieval**: Previous discussions, code patterns, best practices
- **Continuity**: New team members can access full project history

### Customer Support
Provide personalized support with full interaction history:

**Scenario**: Technical support agent
- **Customer History**: Previous tickets, solutions, preferences
- **Knowledge Base**: Product documentation, troubleshooting guides
- **Escalation Context**: Full conversation history for specialists

### Research & Analysis
Accumulate and synthesize information over time:

**Scenario**: Market research project
- **Data Collection**: Articles, reports, interview notes
- **Pattern Recognition**: Identify trends and insights
- **Report Generation**: Synthesize findings with full source attribution

---

## 🔧 Advanced Configuration

### Vector Database Setup

**Qdrant Configuration:**
```yaml
# qdrant-config.yaml
qdrant:
  host: qdrant.soma-agent-hub.svc.cluster.local
  port: 6333
  collection_config:
    vector_size: 1536
    distance: Cosine
    on_disk_payload: true
  performance:
    max_indexing_threads: 4
    indexing_threshold: 20000
```

**Memory Optimization:**
```python
# Configure memory optimization
memory_client.configure_optimization(
    auto_summarization=True,
    relevance_threshold=0.7,
    compression_enabled=True,
    cleanup_schedule="daily"
)
```

### Custom Embeddings

**Use Custom Embedding Models:**
```python
from somaagent.memory import EmbeddingProvider

# Configure custom embeddings
embedding_provider = EmbeddingProvider(
    model="sentence-transformers/all-MiniLM-L6-v2",
    device="cuda",
    batch_size=32
)

memory_client.set_embedding_provider(embedding_provider)
```

### Memory Analytics

**Track Memory Usage:**
```python
# Get memory statistics
stats = memory_client.get_statistics()
print(f"Total documents: {stats.document_count}")
print(f"Storage used: {stats.storage_mb}MB")
print(f"Search queries: {stats.search_count}")

# Memory health check
health = memory_client.health_check()
assert health.status == "healthy"
```

---

## 🔍 Monitoring & Troubleshooting

### Memory Metrics

**Key Metrics to Monitor:**
- **Storage Usage**: Total memory consumption
- **Query Latency**: Search response times
- **Hit Rate**: Successful memory retrievals
- **Index Health**: Vector database performance

**Grafana Dashboard Queries:**
```promql
# Memory storage usage
sum(qdrant_collection_vectors_count) by (collection)

# Search latency P95
histogram_quantile(0.95, rate(memory_search_duration_seconds_bucket[5m]))

# Memory hit rate
rate(memory_search_hits_total[5m]) / rate(memory_search_total[5m])
```

### Common Issues

**High Memory Usage:**
```bash
# Check memory statistics
soma memory stats --detailed

# Clean up old contexts
soma memory cleanup --older-than 30d

# Optimize vector index
soma memory optimize --collection agents
```

**Slow Search Performance:**
```bash
# Check index health
soma memory health-check

# Rebuild index if needed
soma memory reindex --collection knowledge_base

# Adjust search parameters
soma config set memory.search_timeout 5s
```

**Context Not Found:**
```bash
# Verify context exists
soma memory search --agent-id agent-123 --session-id session-456

# Check retention policies
soma config get memory.retention_policies

# Restore from backup if needed
soma memory restore --backup-id backup-20241201
```

---

## 🛡️ Security & Privacy

### Data Protection

**Encryption:**
- **At Rest**: AES-256 encryption for stored vectors and metadata
- **In Transit**: TLS 1.3 for all memory operations
- **Key Management**: Integration with Vault for key rotation

**Access Control:**
```yaml
# memory-rbac.yaml
roles:
  - name: memory-admin
    permissions:
      - memory:read
      - memory:write
      - memory:delete
      - memory:admin
  - name: agent-user
    permissions:
      - memory:read
      - memory:write
    restrictions:
      - own_contexts_only: true
```

### Privacy Compliance

**Data Classification:**
```python
# Classify sensitive data
memory_client.store_document(
    content="Customer payment information...",
    classification="confidential",
    retention_override="30d",
    encryption_level="high"
)
```

**PII Handling:**
```python
# Automatic PII detection and anonymization
memory_client.configure_pii_protection(
    detect_pii=True,
    anonymize_pii=True,
    pii_types=["email", "phone", "ssn", "credit_card"]
)
```

---

## 📊 Performance Optimization

### Indexing Strategies

**Optimize for Search Speed:**
```python
# Configure index parameters
memory_client.configure_index(
    index_type="hnsw",
    m=16,
    ef_construct=200,
    ef_search=100
)
```

**Batch Operations:**
```python
# Batch document storage
documents = [
    {"content": doc1, "metadata": meta1},
    {"content": doc2, "metadata": meta2},
    # ... more documents
]

memory_client.batch_store(documents, batch_size=100)
```

### Memory Lifecycle Management

**Automatic Cleanup:**
```python
# Configure automatic cleanup
memory_client.configure_lifecycle(
    auto_cleanup=True,
    cleanup_schedule="0 2 * * *",  # Daily at 2 AM
    retention_rules={
        "temporary": "7d",
        "conversation": "30d",
        "knowledge": "1y"
    }
)
```

---

## 🔗 Integration Examples

### Workflow Integration

**Memory-Aware Workflows:**
```python
@workflow.defn
class MemoryAwareWorkflow:
    @workflow.run
    async def run(self, request: WorkflowRequest) -> WorkflowResult:
        # Retrieve relevant context
        context = await workflow.execute_activity(
            retrieve_memory_context,
            request.agent_id,
            request.session_id
        )
        
        # Process with context
        result = await workflow.execute_activity(
            process_with_memory,
            request.input,
            context
        )
        
        # Store updated context
        await workflow.execute_activity(
            store_memory_context,
            request.agent_id,
            request.session_id,
            result.context
        )
        
        return result
```

### API Integration

**REST API Access:**
```bash
# Store memory via API
curl -X POST http://gateway:10000/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-123",
    "content": "Important project decision...",
    "metadata": {"type": "decision", "project": "alpha"}
  }'

# Search memory via API
curl -X GET "http://gateway:10000/v1/memory/search?q=project%20decision&agent_id=agent-123"
```

---

## 📞 Getting Help

### Documentation
- **[Memory Gateway Technical Manual](../../technical-manual/memory-gateway.md)** - Deployment and configuration
- **[API Reference](../../development-manual/api-reference.md#memory-api)** - Complete API documentation
- **[Troubleshooting Guide](../troubleshooting.md#memory-issues)** - Common issues and solutions

### Support Channels
- **Slack**: `#soma-memory` for memory-specific questions
- **GitHub**: Issues tagged with `memory` or `qdrant`
- **Documentation**: Memory-related runbooks and guides

### Advanced Topics
- **Custom Embedding Models** - Integrate domain-specific embeddings
- **Multi-Modal Memory** - Store and search images, audio, and documents
- **Federated Memory** - Distribute memory across multiple clusters
- **Memory Analytics** - Advanced usage patterns and optimization

---

**Ready to enhance your agents with intelligent memory? Start by enabling the Memory Gateway in your SomaAgentHub deployment and configuring your first memory-aware agent workflow.**