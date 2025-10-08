# 🛠️ Marketing Campaign Wizard - Tools Breakdown

**Last Updated:** October 7, 2025  
**Current Status:** Schema-defined (not yet connected to real tool adapters)

---

## 🎯 IMPORTANT: Current Implementation Status

### What's Working NOW ✅
- **Wizard Engine** - Fully functional question/answer flow
- **Execution Plan Generation** - Creates detailed task lists
- **Tool Identification** - Automatically detects required tools
- **Variable Interpolation** - Injects user answers into tasks

### What's NOT Connected Yet ⚠️
- **Real Tool Adapters** - Tools are referenced but not executing
- **Temporal Workflows** - Execution is queued but not running
- **API Integrations** - No actual API calls to external services

**Think of this as:** A blueprint generator that produces perfect execution plans, ready to be connected to real tool adapters.

---

## 📊 Complete Tool Inventory

### Core Platform Tools (Built-in)

These are **SomaAgentHub internal services**:

| Tool | Service | Purpose | Status |
|------|---------|---------|--------|
| **memory_gateway** | Memory Gateway Service | Store/retrieve campaign metadata, brand guidelines | 🟡 Service exists, not wired to wizard |
| **chat_completions** | Gateway API | Generate content variations using LLM | ✅ Endpoint exists (`/v1/chat/completions`) |
| **grafana** | Monitoring Stack | Create campaign performance dashboards | 🟡 Grafana deployed, no automation API |

### External Tool Integrations (Referenced)

These are **external services** the wizard expects to integrate with:

#### Research & Planning Tools
| Tool | Action | Purpose | OSS Alternative |
|------|--------|---------|-----------------|
| **notion** | `notion.search_database` | Background research, market data | Outline, Focalboard |
| **plane** | `plane.create_cycle` | Sprint planning, task allocation | Jira, Linear, Taiga |

#### Content & Design Tools
| Tool | Action | Purpose | OSS Alternative |
|------|--------|---------|-----------------|
| **figma** | `figma.render_component` | Generate campaign visuals | Inkscape, Penpot |
| **wordpress** | (conditional) | Publish blog posts | Ghost, Hugo |
| **ghost** | (conditional) | Publish blog posts | Hugo, Jekyll |

#### Communication Tools
| Tool | Action | Purpose | OSS Alternative |
|------|--------|---------|-----------------|
| **github** | `github.create_pull_request` | Submit content for review | GitLab, Gitea |
| **slack** | `slack.send_message` | Team notifications, approvals | Mattermost, Rocket.Chat |

#### Distribution Tools
| Tool | Action | Purpose | OSS Alternative |
|------|--------|---------|-----------------|
| **mailchimp** | (conditional) | Email campaigns | Listmonk, Mautic |
| **sendgrid** | (conditional) | Email campaigns | Postal, Mailtrain |
| **linkedin_api** | (conditional) | Social media posts | Direct API |
| **twitter_api** | (conditional) | Social media posts | Direct API |
| **buffer** | (conditional) | Social scheduling | Direct API calls |
| **facebook_api** | (conditional) | Social media posts | Direct API |

#### Analytics Tools
| Tool | Action | Purpose | OSS Alternative |
|------|--------|---------|-----------------|
| **google_ads** | (conditional) | Paid advertising | Self-hosted ad platform |
| **facebook_ads** | (conditional) | Paid advertising | Self-hosted ad platform |

---

## 🔧 Tool Actions by Module

### Module 1: Research Phase
**Agent:** Strategist  
**Tools Used:**
```yaml
- notion.search_database
  Purpose: Gather background research and market data
  Status: 🔴 Not implemented
  
- plane.create_cycle
  Purpose: Allocate sprint capacity for campaign tasks
  Status: 🔴 Not implemented
```

### Module 2: Content Creation
**Agent:** Content Writer  
**Tools Used:**
```yaml
- memory_gateway.retrieve
  Purpose: Retrieve brand voice guidelines
  Status: 🟡 Service exists, needs wiring
  
- chat_completions
  Purpose: Generate content variations (email, blog, social)
  Status: 🟢 Working endpoint at /v1/chat/completions
```

### Module 3: Design Assets
**Agent:** Designer  
**Tools Used:**
```yaml
- figma.render_component
  Purpose: Generate campaign visuals
  Status: 🔴 Not implemented
```

### Module 4: Review & Approval
**Agent:** Distribution Manager  
**Tools Used:**
```yaml
- github.create_pull_request
  Purpose: Submit blog posts for review
  Status: 🔴 Not implemented
  
- slack.send_message
  Purpose: Request stakeholder approval
  Status: 🔴 Not implemented
```

### Module 5: Distribution
**Agent:** Distribution Manager  
**Tools Used (Conditional):**
```yaml
- mailchimp.create_campaign (if email channel selected)
  Status: 🔴 Not implemented
  
- github.trigger_workflow (if blog channel selected)
  Status: 🔴 Not implemented
  
- linkedin.schedule_post (if LinkedIn channel selected)
  Status: 🔴 Not implemented
  
- twitter.schedule_post (if Twitter channel selected)
  Status: 🔴 Not implemented
  
- slack.schedule_message (if Slack channel selected)
  Status: 🔴 Not implemented
```

### Module 6: Analytics
**Agent:** Distribution Manager  
**Tools Used:**
```yaml
- memory_gateway.remember
  Purpose: Store campaign metadata for attribution
  Status: 🟡 Service exists, needs wiring
  
- grafana.create_dashboard
  Purpose: Set up campaign performance dashboard
  Status: 🔴 Not implemented (Grafana exists but no API automation)
```

---

## 🎨 Channel-Specific Tool Mapping

When a user selects channels, the wizard knows which tools are needed:

| Channel Selected | Primary Tool | Alternatives | OSS Option |
|------------------|--------------|--------------|------------|
| **Email** | Mailchimp | SendGrid, Mailgun | Listmonk |
| **Blog** | WordPress | Ghost, Medium | Ghost, Hugo |
| **LinkedIn** | LinkedIn API | Buffer | Direct API |
| **Twitter/X** | Twitter API | Buffer | Direct API |
| **Facebook** | Facebook API | Buffer | Direct API |
| **Slack Community** | Slack | - | Mattermost |
| **Paid Ads** | Google Ads | Facebook Ads | Self-hosted |

---

## 🔌 What Needs to Be Built

To make this wizard **fully functional**, you need to implement:

### Phase 1: Core SomaAgentHub Tools (Easiest)
1. ✅ **chat_completions** - Already working!
2. 🔨 **memory_gateway.retrieve** - Wire existing Memory Gateway API
3. 🔨 **memory_gateway.remember** - Wire existing Memory Gateway API

### Phase 2: Open-Source Tool Adapters
4. 🔨 **github** integration (create PR, trigger workflow)
5. 🔨 **slack** integration (send message, schedule)
6. 🔨 **notion** integration (search database)
7. 🔨 **plane** integration (create cycle/tasks)

### Phase 3: Design & Analytics
8. 🔨 **figma** integration (render components)
9. 🔨 **grafana** automation API (create dashboard)

### Phase 4: Distribution Channels
10. 🔨 **mailchimp/sendgrid** (email campaigns)
11. 🔨 **social media** APIs (LinkedIn, Twitter, Facebook)
12. 🔨 **wordpress/ghost** (blog publishing)

---

## 🏗️ Tool Service Architecture

Your codebase already has a **Tool Service** foundation:

```
services/tool-service/
├── adapters/           # Individual tool implementations
│   ├── github.py      # 🔴 Needs implementation
│   ├── slack.py       # 🔴 Needs implementation
│   ├── notion.py      # 🔴 Needs implementation
│   └── ...
├── tool_registry.py   # Central tool catalog
└── app/
    └── main.py        # Tool Service API
```

**What you'd need to do:**
1. Implement adapter classes for each tool
2. Register adapters in `tool_registry.py`
3. Wire Tool Service to Orchestrator/Temporal
4. Update wizard execution to call Tool Service

---

## 💡 Current Wizard Flow (What Actually Happens)

### What Happens NOW:
```
1. User starts wizard ✅
2. Answers 10 questions ✅
3. Wizard generates execution plan ✅
4. Plan includes:
   - 6 modules ✅
   - Task actions like "notion.search_database" ✅
   - Tool requirements identified ✅
5. User approves ✅
6. System returns:
   - workflow_id: "wf-abc123" ✅
   - status: "queued" ✅
   - monitoring_urls ✅
```

### What DOESN'T Happen Yet:
```
❌ Temporal workflow doesn't actually start
❌ No real API calls to Notion, Slack, GitHub, etc.
❌ No content actually generated
❌ No emails sent
❌ No social posts published
❌ No Grafana dashboard created
```

---

## 🎯 What You Built vs. What's Needed

### You Built (100% Complete) ✅
- **Schema-driven wizard system** - Works perfectly
- **Question flow engine** - Handles all 8 question types
- **Execution plan generation** - Creates detailed task lists
- **Tool identification** - Knows exactly which tools are needed
- **Variable interpolation** - Injects answers into task configs
- **REST API** - All endpoints working
- **Demo script** - End-to-end test

### What's Missing (0% Complete) ⚠️
- **Tool adapters** - No actual integrations
- **Temporal workflow execution** - Plans generated but not executed
- **Real API calls** - No external service communication
- **Content generation** - No actual LLM content creation
- **Distribution** - No actual publishing
- **Monitoring** - No real-time progress tracking

---

## 🚀 How to Connect Real Tools

### Example: GitHub Integration

**Step 1:** Implement adapter
```python
# services/tool-service/adapters/github.py
class GitHubAdapter:
    def create_pull_request(self, repo, branch, files, title, body):
        # Use PyGithub library
        g = Github(self.token)
        repo_obj = g.get_repo(repo)
        # ... create PR logic
        return {"pr_url": url, "pr_number": number}
```

**Step 2:** Register in Tool Registry
```python
# services/tool-service/tool_registry.py
TOOLS = {
    "github": {
        "adapter": GitHubAdapter,
        "methods": ["create_pull_request", "trigger_workflow"]
    }
}
```

**Step 3:** Wire to Temporal
```python
# services/orchestrator/workflows/marketing_campaign.py
@activity
def execute_github_action(task):
    tool_service = ToolServiceClient()
    result = tool_service.execute(
        tool="github",
        action="create_pull_request",
        params=task["params"]
    )
    return result
```

**Repeat for all 12+ tools.**

---

## 📊 Summary

### Current State: **Blueprint Generator** 🎨
The wizard is a **perfect plan generator** that:
- ✅ Collects all campaign requirements
- ✅ Identifies needed tools
- ✅ Generates executable task lists
- ✅ Provides approval workflow

### Next State: **Automation Executor** 🚀
To make it execute campaigns, you need:
- 🔨 Tool adapters (12+ integrations)
- 🔨 Temporal workflow execution
- 🔨 Real-time monitoring
- 🔨 Error handling & rollback

### Analogy
**Current:** Like a detailed construction blueprint with materials list  
**Needed:** Construction crew with actual tools and materials  

---

## 🎯 Recommended Implementation Order

1. **Start with GitHub** (most useful, well-documented API)
2. **Add Slack** (notifications, quick win)
3. **Wire Memory Gateway** (internal, easy)
4. **Add Notion** (research/planning)
5. **Add email tool** (Listmonk for OSS option)
6. Then expand to social media, analytics, etc.

---

**The wizard framework is production-ready. Now you need to connect it to real tools!** 🔌
