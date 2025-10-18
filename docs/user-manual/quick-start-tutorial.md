# Quick Start Tutorial

**Your first autonomous agent workflow in 15 minutes**

> This tutorial walks you through creating and executing your first multi-agent workflow using SomaAgentHub's wizard interface.

---

## 🎯 What You'll Learn

By the end of this tutorial, you'll have:
- ✅ Created your first agent workflow
- ✅ Monitored workflow execution in real-time  
- ✅ Understood approval and governance processes
- ✅ Reviewed workflow results and artifacts

**Time Required:** 15 minutes  
**Difficulty:** Beginner

---

## 📋 Prerequisites

- ✅ Access to SomaAgentHub web interface
- ✅ Valid user account with workflow creation permissions
- ✅ Completed [Installation & Access](installation.md) setup

---

## 🚀 Step 1: Access the Wizard Interface

### Login to SomaAgentHub

1. **Open your browser** and navigate to your SomaAgentHub instance
2. **Login** with your credentials
3. **Verify** you see the main dashboard

### Navigate to Wizards

1. **Click "Wizards"** in the main navigation
2. **View available wizards** - you should see several options:
   - 📝 **Document Analysis Wizard**
   - 🏗️ **Project Creation Wizard** 
   - 📊 **Data Processing Wizard**
   - 🔍 **Research Assistant Wizard**

---

## 🏗️ Step 2: Start Your First Workflow

### Select the Document Analysis Wizard

1. **Click "Document Analysis Wizard"**
2. **Read the description**: "Analyze documents using multiple AI agents for comprehensive insights"
3. **Click "Start Wizard"**

### Configure Your Workflow

**Step 1 - Basic Information:**
```
Workflow Name: My First Analysis
Description: Tutorial workflow for document analysis
Priority: Normal
```

**Step 2 - Document Upload:**
1. **Upload a sample document** (PDF, Word, or text file)
2. **Or use the provided sample**: "Sample Business Report.pdf"
3. **Specify analysis type**: "Comprehensive Analysis"

**Step 3 - Agent Configuration:**
```
✅ Content Summarizer Agent
✅ Sentiment Analysis Agent  
✅ Key Insights Extractor Agent
✅ Recommendation Generator Agent
```

**Step 4 - Output Preferences:**
```
Format: Executive Summary + Detailed Report
Delivery: Email notification + Dashboard
Approval Required: Yes (for tutorial purposes)
```

### Launch the Workflow

1. **Review your configuration** in the summary screen
2. **Click "Launch Workflow"**
3. **Note your Workflow ID**: `workflow-abc123` (save this!)

---

## 📊 Step 3: Monitor Workflow Execution

### Real-Time Dashboard

1. **Navigate to "Active Workflows"** from the main menu
2. **Find your workflow** in the list
3. **Click to view details**

### Workflow Progress

You'll see the workflow progressing through stages:

```
🟢 Stage 1: Document Processing (Complete)
🟡 Stage 2: Content Analysis (In Progress)
⚪ Stage 3: Sentiment Analysis (Queued)
⚪ Stage 4: Insights Extraction (Queued)  
⚪ Stage 5: Report Generation (Queued)
⚪ Stage 6: Human Approval (Pending)
```

### Agent Activity

**Monitor individual agents:**
- **Content Summarizer**: Processing document sections
- **Sentiment Analyzer**: Analyzing tone and sentiment
- **Insights Extractor**: Identifying key themes
- **Report Generator**: Compiling final output

**Estimated completion time:** 5-8 minutes

---

## ✋ Step 4: Handle Approval Workflow

### Approval Notification

After ~5 minutes, you'll receive:
- 📧 **Email notification**: "Workflow approval required"
- 🔔 **Dashboard alert**: Red notification badge
- 📱 **Mobile push** (if configured)

### Review and Approve

1. **Click the notification** or navigate to "Pending Approvals"
2. **Review the generated analysis**:
   - Executive summary
   - Key findings
   - Sentiment analysis results
   - Recommended actions

3. **Approve or Request Changes**:
   ```
   ✅ Approve: Continue to final report generation
   🔄 Request Changes: Specify modifications needed
   ❌ Reject: Cancel workflow with reason
   ```

4. **For this tutorial, click "Approve"**

---

## 📋 Step 5: Review Results

### Final Report Generation

After approval, the workflow completes:
```
🟢 All Stages Complete
📊 Final Report Generated
📧 Notification Sent
💾 Artifacts Stored
```

### Access Your Results

**Dashboard View:**
1. **Navigate to "Completed Workflows"**
2. **Click your workflow ID**
3. **View the executive summary**

**Detailed Report:**
1. **Click "Download Full Report"** (PDF format)
2. **Review sections**:
   - Document overview
   - Content analysis
   - Sentiment insights  
   - Key recommendations
   - Agent execution logs

**Artifacts:**
- 📄 **Original document** (with annotations)
- 📊 **Analysis charts** (sentiment trends, key themes)
- 📝 **Executive summary** (1-page overview)
- 🔍 **Detailed findings** (multi-page report)

---

## 🎉 Congratulations!

You've successfully:
- ✅ **Created** your first multi-agent workflow
- ✅ **Monitored** real-time execution across multiple agents
- ✅ **Participated** in the approval process
- ✅ **Received** comprehensive analysis results

---

## 🔄 What Happened Behind the Scenes?

### Agent Orchestration
1. **Gateway API** received your wizard request
2. **Orchestrator** launched a Temporal workflow
3. **Multiple agents** executed in parallel and sequence
4. **Policy Engine** enforced approval requirements
5. **Memory Gateway** stored context between steps

### Infrastructure
- **Kubernetes pods** scaled automatically for agent workloads
- **Redis** maintained session state across interactions
- **PostgreSQL** stored workflow metadata and results
- **Qdrant** provided vector storage for document embeddings

---

## 🚀 Next Steps

### Explore More Features

**Try Different Wizards:**
- 🏗️ **Project Creation**: Build a complete software project
- 📊 **Data Processing**: Analyze datasets with multiple agents
- 🔍 **Research Assistant**: Comprehensive research workflows

**Advanced Capabilities:**
- **Custom Agent Configurations**: Modify agent parameters
- **Integration Workflows**: Connect external systems
- **Scheduled Workflows**: Automate recurring tasks

### Learn More

1. **Read [Core Features](features/index.md)** for detailed capabilities
2. **Explore [Workflow Management](features/workflow-management.md)** for advanced patterns
3. **Check [FAQ](faq.md)** for common questions
4. **Join training sessions** offered by your organization

---

## 🔧 Troubleshooting

**Workflow Stuck?**
- Check the "Agent Logs" tab for error details
- Verify document format is supported
- Contact administrator if issues persist

**Approval Not Received?**
- Check email spam folder
- Verify notification preferences in your profile
- Use dashboard "Pending Approvals" section

**Results Missing?**
- Workflows are retained for 90 days by default
- Check "Archived Workflows" for older results
- Contact support for data recovery

---

**Ready to orchestrate more complex workflows? Explore the [Core Features](features/index.md) to unlock the full power of SomaAgentHub!**