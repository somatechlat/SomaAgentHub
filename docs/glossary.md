# SomaAgentHub Glossary

**A comprehensive glossary of terms, concepts, and technologies used in the SomaAgentHub project.**

---

## A

**Agent**
: An autonomous, AI-powered entity designed to perform a specific task or set of tasks. Agents are the fundamental actors in the SomaAgentHub ecosystem.

**API Gateway**
: The single entry point for all external traffic to the platform. It handles authentication, rate limiting, and routing to the appropriate microservice.

**Asynchronous**
: Operations that are performed in the background, without blocking the main application thread. Our workflows are asynchronous.

## C

**Changelog**
: A file that keeps a chronological record of all notable changes made to the project.

**Conventional Commits**
: A specification for adding human and machine-readable meaning to commit messages.

## D

**Docker**
: A platform for developing, shipping, and running applications in containers. We use it for local development and as the container runtime in Kubernetes.

## G

**Gateway API**
: See **API Gateway**.

## H

**Helm**
: The package manager for Kubernetes. We use Helm to define, install, and upgrade the entire SomaAgentHub application.

## I

**Identity Service**
: The microservice responsible for managing users, authentication (JWTs), and authorization (RBAC).

## K

**Kubernetes (K8s)**
: An open-source container orchestration system for automating software deployment, scaling, and management.

## M

**Memory Gateway**
: The microservice that provides long-term, semantic memory for agents, using a vector database.

**Microservice**
: An architectural style that structures an application as a collection of loosely coupled, independently deployable services.

**Multi-Agent Orchestration**
: The core concept of SomaAgentHub; the process of coordinating multiple specialized agents to achieve a complex goal.

## O

**Observability**
: The practice of designing systems to be understood from the outside. In our context, it refers to our metrics (Prometheus), logging (Loki), and tracing stack.

**Orchestrator**
: The core microservice that manages the lifecycle of multi-agent workflows using Temporal.

## P

**Policy Engine**
: The microservice that enforces safety, ethical, and operational rules ("constitutional AI") on agent behavior.

**PostgreSQL**
: The primary relational database used for storing structured data like user information and policies.

**Prometheus**
: The monitoring tool we use to collect and store time-series metrics from our services.

**Pytest**
: The primary framework we use for writing and running Python tests.

## Q

**Qdrant**
: The vector database used by the Memory Gateway for high-performance semantic search.

## R

**RBAC (Role-Based Access Control)**
: A method of restricting system access to authorized users based on their role.

**Redis**
: An in-memory data store used for caching and session management.

**Ruff**
: The extremely fast Python linter and code formatter we use to maintain code quality.

## S

**Semantic Search**
: A search technique that understands the intent and contextual meaning of words, rather than just matching keywords. This is the core of our Memory Gateway.

## T

**Temporal**
: The durable execution system that powers our asynchronous, long-running workflows in the Orchestrator.

**Terraform**
: An infrastructure as code (IaC) tool used to provision and manage cloud resources.
```
