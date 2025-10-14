# SomaAgentHub Use Cases

This document provides a collection of practical use cases for the SomaAgentHub platform, demonstrating how to combine its services to solve real-world problems.

## 1. Automated Employee Onboarding

**Goal:** Automate the process of onboarding a new employee, from creating accounts to assigning training materials.

**Services Used:**

*   **Orchestrator Service:** To manage the overall onboarding workflow.
*   **Identity Service:** To create user accounts.
*   **Tool Service:** To interact with external systems like Slack and Notion.
*   **Notification Service:** To send welcome emails and notifications.

**Workflow:**

1.  An HR manager initiates the onboarding workflow via the Orchestrator Service, providing the new employee's details.
2.  The orchestrator starts a Temporal workflow that coordinates the following tasks:
    *   Creates a user account in the Identity Service.
    *   Uses the Tool Service to:
        *   Create a Slack account and invite the user to relevant channels.
        *   Create a Notion account and share the onboarding documentation.
    *   Sends a welcome email via the Notification Service.
3.  The workflow tracks the progress of each task and sends a final notification to the HR manager upon completion.

## 2. Multi-Channel Marketing Campaign

**Goal:** Launch a marketing campaign across multiple channels, including email, social media, and a blog.

**Services Used:**

*   **Multi-Agent Orchestrator (MAO):** To coordinate the activities of multiple agents.
*   **SLM Service:** For content generation.
*   **Tool Service:** To interact with marketing platforms.
*   **Analytics Service:** To track campaign performance.

**Workflow:**

1.  A marketing manager starts a multi-agent orchestration with the following directives:
    *   **Strategist Agent:** Researches the target audience and develops a campaign strategy.
    *   **Content Agent:** Generates content for each channel using the SLM Service.
    *   **Distribution Agent:** Schedules and publishes the content using the Tool Service.
2.  The MAO coordinates the agents, ensuring that the content is generated before it is distributed.
3.  The Analytics Service tracks the performance of the campaign and provides real-time feedback to the marketing manager.

## 3. Incident Response and Postmortem

**Goal:** Automate the process of responding to a production incident, from creating a war room to generating a postmortem report.

**Services Used:**

*   **Orchestrator Service:** To manage the incident response workflow.
*   **Tool Service:** To interact with systems like Slack, Jira, and Datadog.
*   **Memory Gateway:** To store information about the incident for later analysis.
*   **SLM Service:** To generate the postmortem report.

**Workflow:**

1.  An alert from a monitoring system triggers the incident response workflow in the Orchestrator Service.
2.  The workflow creates a Slack channel for the war room and invites the on-call engineers.
3.  The workflow uses the Tool Service to gather information from various systems and stores it in the Memory Gateway.
4.  Once the incident is resolved, the workflow uses the SLM Service to generate a postmortem report based on the information in the Memory Gateway.
5.  The postmortem report is then shared with the relevant stakeholders.
