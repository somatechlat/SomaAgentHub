# SomaAgentHub Examples Testing Roadmap

## 🎯 OBJECTIVE
Test every example in the examples/ directory to determine what actually works vs what's just demo code.

## 📊 CURRENT STATE ANALYSIS

### Services Running:
- ✅ Gateway API (port 10000) - Basic HTTP responses
- ✅ Orchestrator (port 10001) - Basic HTTP responses  
- ❌ Temporal Server - NOT RUNNING
- ❌ Redis - NOT RUNNING
- ❌ Identity Service - NOT RUNNING

### What We Learned from wizard-demo.sh:
- Gateway API responds with hardcoded JSON
- No actual AI agents execute
- Final execution fails with "Internal Server Error"
- This is a **UI demo**, not real orchestration

## 🗺️ TESTING PHASES

### Phase 1: Infrastructure Setup (30 min)
**Goal**: Get all required services actually running

#### Step 1.1: Check Dependencies
```bash
# Check what's actually needed
docker ps
kubectl get pods
make dev-up status
```

#### Step 1.2: Start Missing Services
```bash
# Try to start full stack
make dev-up
make dev-start-services
```

#### Step 1.3: Verify All Services
```bash
curl http://localhost:10000/health
curl http://localhost:10001/health  
curl http://localhost:10002/health  # Identity
curl http://localhost:10009/health  # Temporal
```

### Phase 2: SDK Examples Testing (45 min)
**Goal**: Test examples that use the Python SDK

#### Example 2.1: agent_call_example.py
**Expected**: Basic API call to Gateway
**Dependencies**: Gateway API, Python SDK
**Test**:
```bash
cd examples/
python agent_call_example.py --message "Hello" --api-url http://localhost:10000
```
**Success Criteria**: Gets response without error

#### Example 2.2: accounting_software_demo.py  
**Expected**: Interactive wizard simulation
**Dependencies**: None (pure Python)
**Test**:
```bash
python accounting_software_demo.py
# Answer prompts interactively
```
**Success Criteria**: Generates project_plan_accounting_ecuador.json

#### Example 2.3: chatbot/app.py
**Expected**: Interactive chatbot with Rich UI
**Dependencies**: Gateway API, somaagent SDK, SOMAAGENT_API_KEY
**Test**:
```bash
cd chatbot/
export SOMAAGENT_API_KEY="test-key"
python app.py
```
**Success Criteria**: Starts without crashing, can send messages

#### Example 2.4: code-assistant/app.py
**Expected**: Code review assistant
**Dependencies**: Gateway API, somaagent SDK, SOMAAGENT_API_KEY
**Test**:
```bash
cd code-assistant/
export SOMAAGENT_API_KEY="test-key"  
python app.py
```
**Success Criteria**: Menu appears, can select options

#### Example 2.5: data-analysis/app.py
**Expected**: Data analysis with pandas
**Dependencies**: Gateway API, somaagent SDK, pandas, SOMAAGENT_API_KEY
**Test**:
```bash
cd data-analysis/
pip install pandas
export SOMAAGENT_API_KEY="test-key"
python app.py
```
**Success Criteria**: Starts, can load CSV files

### Phase 3: Orchestration Examples Testing (60 min)
**Goal**: Test examples that claim to do multi-agent orchestration

#### Example 3.1: mao-project/create_project.py
**Expected**: Multi-agent project creation
**Dependencies**: MAO service (localhost:10001), real orchestration
**Test**:
```bash
cd mao-project/
python create_project.py
```
**Success Criteria**: Creates project, shows real progress

#### Example 3.2: kamachiq-demo/autonomous_project_demo.py
**Expected**: Full autonomous project creation
**Dependencies**: All services, KAMACHIQ components, tool integrations
**Test**:
```bash
cd kamachiq-demo/
python autonomous_project_demo.py
```
**Success Criteria**: Runs without import errors, shows real automation

### Phase 4: Integration Reality Check (30 min)
**Goal**: Determine what's real vs demo

#### Test 4.1: Check SDK Implementation
```bash
# Examine the actual SDK
ls -la sdk/python/somaagent/
cat sdk/python/somaagent/client.py
```

#### Test 4.2: Check Service Implementations  
```bash
# Check what Gateway API actually does
cat services/gateway-api/app/main.py
cat services/orchestrator/app/main.py
```

#### Test 4.3: Check Tool Integrations
```bash
# See if tool adapters are real
ls -la services/tool-service/adapters/
cat services/tool-service/adapters/github_adapter.py
```

## 📝 TESTING RESULTS TEMPLATE

### Example: [NAME]
- **Status**: ✅ Works / ❌ Fails / ⚠️ Partial
- **Dependencies Met**: Yes/No
- **Actual Behavior**: [What actually happens]
- **Expected vs Reality**: [Comparison]
- **Errors**: [Any error messages]
- **Conclusion**: [Real functionality vs demo]

## 🎯 SUCCESS CRITERIA

### Minimum Viable Reality:
- [ ] At least 3 examples work end-to-end
- [ ] SDK can make real API calls
- [ ] At least 1 example shows real agent coordination
- [ ] Clear distinction between demos and real functionality

### Full Success:
- [ ] All examples work as documented
- [ ] Multi-agent orchestration actually works
- [ ] Tool integrations are functional
- [ ] Real AI agents execute tasks

## ⏱️ TIME ESTIMATE
**Total**: 2.5 hours
- Phase 1: 30 min
- Phase 2: 45 min  
- Phase 3: 60 min
- Phase 4: 30 min
- Documentation: 15 min

## 🚨 CRITICAL QUESTIONS TO ANSWER

1. **Does the Python SDK actually work?**
2. **Are there real AI agents or just hardcoded responses?**
3. **Does multi-agent orchestration actually happen?**
4. **Which tool integrations are real vs placeholder?**
5. **What requires external API keys (OpenAI, etc.)?**
6. **What's the minimum setup for real functionality?**

---

**NEXT STEP**: Execute Phase 1 to get infrastructure running properly.