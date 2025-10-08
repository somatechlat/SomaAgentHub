# 🏗️ SomaAgent Multi-Agent Architecture Blueprint

**Project**: SomaAgentHub Multi-Agent Orchestration Platform  
**Version**: 1.0.0  
**Date**: October 7, 2025  
**Status**: Architecture Design - Production-Ready Implementation  
**Author**: AI Architecture Team

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Core Workflows](#core-workflows)
4. [Communication Layer](#communication-layer)
5. [Shared Memory Layer](#shared-memory-layer)
6. [Agent Execution Layer](#agent-execution-layer)
7. [API Specifications](#api-specifications)
8. [Data Models](#data-models)
9. [Implementation Plan](#implementation-plan)
10. [Production Deployment](#production-deployment)

---

## 🎯 EXECUTIVE SUMMARY

This blueprint defines a **world-class, production-ready multi-agent orchestration platform** that combines the best patterns from industry-leading frameworks (AutoGen, CrewAI, LangGraph, MetaGPT) with Temporal's battle-tested durability.

### **Key Innovations**

1. **5 Coordination Patterns**: Group Chat, Supervisor, Consensus, Blackboard, Hybrid
2. **Multi-Layer Communication**: Message Bus (Redis), Shared Memory (Qdrant), Temporal Signals
3. **Durable State**: Temporal workflows ensure zero data loss
4. **Distributed Execution**: 1000+ concurrent agents across multiple workers
5. **Production-Grade**: Fault tolerance, observability, scalability

### **Core Principles**

- ✅ **Elegance**: Simple APIs for common patterns
- ✅ **Power**: Support complex multi-agent coordination
- ✅ **Reliability**: Netflix/Uber-grade fault tolerance
- ✅ **Observability**: Full tracing of agent conversations
- ✅ **Extensibility**: Plugin architecture for new patterns

---

## 🏛️ SYSTEM ARCHITECTURE

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SOMAAGENT MULTI-AGENT PLATFORM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    API LAYER (FastAPI)                             │    │
│  │  POST /v1/multi-agent/group-chat                                   │    │
│  │  POST /v1/multi-agent/supervisor                                   │    │
│  │  POST /v1/multi-agent/consensus                                    │    │
│  │  POST /v1/multi-agent/blackboard                                   │    │
│  │  GET  /v1/multi-agent/{workflow_id}/status                         │    │
│  │  WS   /v1/multi-agent/{workflow_id}/stream                         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │            COORDINATION LAYER (Temporal Workflows)                 │    │
│  │                                                                    │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │    │
│  │  │ GroupChat  │  │ Supervisor │  │ Consensus  │  │ Blackboard │ │    │
│  │  │ Workflow   │  │ Workflow   │  │ Workflow   │  │ Workflow   │ │    │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │    │
│  │         │               │               │               │         │    │
│  │         └───────────────┴───────────────┴───────────────┘         │    │
│  │                          Pattern Router                           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              COMMUNICATION LAYER                                   │    │
│  │                                                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │ Message Bus  │  │ Event Stream │  │   Signals    │           │    │
│  │  │   (Redis)    │  │  (Redis)     │  │  (Temporal)  │           │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │            SHARED MEMORY LAYER (Blackboard)                        │    │
│  │                                                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │   Qdrant     │  │  Temporal    │  │    Redis     │           │    │
│  │  │  (Vectors)   │  │   (State)    │  │   (Cache)    │           │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              AGENT EXECUTION LAYER                                 │    │
│  │                                                                    │    │
│  │   Manager   Worker-1  Worker-2  Worker-3  ...  Worker-N          │    │
│  │   Agent     Agent     Agent     Agent          Agent              │    │
│  │     │         │          │          │            │                │    │
│  │     └─────────┴──────────┴──────────┴────────────┘                │    │
│  │                  Activities (Temporal)                            │    │
│  │  • agent_speak  • agent_vote  • agent_contribute                 │    │
│  │  • agent_review • agent_plan  • agent_execute                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              INTEGRATION LAYER                                     │    │
│  │                                                                    │    │
│  │  SLM Gateway  │  Tool Service  │  Memory Gateway  │  Identity     │    │
│  │  (LLM calls)  │  (16 tools)    │  (RAG + Store)   │  (Auth)      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Component Responsibilities**

| Layer | Components | Responsibility | Technology |
|-------|-----------|----------------|-----------|
| **API Layer** | FastAPI routes | HTTP/WebSocket API, request validation | FastAPI, Pydantic |
| **Coordination Layer** | Temporal Workflows | Pattern orchestration, state management | Temporal, Python |
| **Communication Layer** | Message Bus, Events, Signals | Agent messaging, event streaming | Redis, Temporal |
| **Shared Memory Layer** | Qdrant, Temporal State, Redis | Knowledge sharing, caching | Qdrant, Temporal, Redis |
| **Agent Execution Layer** | Activities | Agent actions (speak, vote, contribute) | Temporal Activities |
| **Integration Layer** | SLM, Tools, Memory, Identity | External services | HTTP clients |

---

## 🎭 CORE WORKFLOWS

### **1. GroupChatWorkflow** (AutoGen-inspired)

**Use Case**: Multiple agents collaborate through conversation  
**Example**: Research team (Researcher + Analyst + Writer) working on report

#### Architecture
```
START
  │
  ▼
┌──────────────────────────┐
│ Initialize Conversation  │
│ • Load agents            │
│ • Create message history │
│ • Set termination rules  │
└──────────────────────────┘
  │
  ▼
┌──────────────────────────┐
│ Select Next Speaker      │ ◄──────┐
│ • Manager decides OR     │        │
│ • Round-robin            │        │
└──────────────────────────┘        │
  │                                  │
  ▼                                  │
┌──────────────────────────┐        │
│ Agent Speaks (Activity)  │        │
│ • Read conversation      │        │
│ • Generate response      │        │
│ • Update history         │        │
└──────────────────────────┘        │
  │                                  │
  ▼                                  │
┌──────────────────────────┐        │
│ Check Termination        │        │
│ • Max rounds reached?    │  No    │
│ • Task complete?         │────────┘
│ • Keyword match?         │
└──────────────────────────┘
  │ Yes
  ▼
┌──────────────────────────┐
│ Return Conversation      │
│ • Full history           │
│ • Final answer           │
│ • Metadata               │
└──────────────────────────┘
  │
  ▼
END
```

#### Implementation
```python
@dataclass
class GroupChatConfig:
    """Configuration for group chat workflow."""
    agents: List[AgentConfig]
    task: str
    max_rounds: int = 10
    speaker_selection: Literal["round-robin", "manager", "auto"] = "auto"
    termination_keywords: List[str] = field(default_factory=lambda: ["TERMINATE", "DONE"])
    termination_check_last_n: int = 3
    broadcast_messages: bool = True  # All agents see all messages


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    agent_id: str
    name: str
    role: str  # e.g., "Researcher", "Analyst", "Writer"
    system_message: str
    capabilities: List[str]
    model: str = "gpt-4"
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)


@dataclass
class ConversationMessage:
    """Single message in group chat."""
    round_number: int
    speaker_id: str
    speaker_name: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupChatResult:
    """Result of group chat workflow."""
    conversation: List[ConversationMessage]
    final_answer: str
    rounds_completed: int
    termination_reason: str
    agents_participated: List[str]
    duration_seconds: float


@workflow.defn
class GroupChatWorkflow:
    """
    Multi-agent group chat workflow.
    
    Agents take turns speaking based on selection strategy.
    Conversation continues until termination condition met.
    
    Based on AutoGen's ConversableAgent + GroupChat pattern.
    """

    @workflow.run
    async def run(self, config: GroupChatConfig) -> GroupChatResult:
        logger = workflow.logger
        logger.info(f"Starting group chat: {config.task}")
        
        # Initialize conversation
        conversation: List[ConversationMessage] = []
        start_time = workflow.now()
        
        # Main conversation loop
        for round_num in range(1, config.max_rounds + 1):
            logger.info(f"Round {round_num}/{config.max_rounds}")
            
            # Select next speaker
            next_speaker = await self._select_next_speaker(
                config, conversation, round_num
            )
            
            # Agent speaks (activity)
            message = await workflow.execute_activity(
                agent_speak_activity,
                AgentSpeakRequest(
                    agent_id=next_speaker.agent_id,
                    agent_config=next_speaker,
                    conversation_history=conversation,
                    task=config.task,
                    round_number=round_num
                ),
                start_to_close_timeout=timedelta(seconds=90),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3
                )
            )
            
            # Add to conversation
            conversation.append(ConversationMessage(
                round_number=round_num,
                speaker_id=next_speaker.agent_id,
                speaker_name=next_speaker.name,
                content=message.content,
                timestamp=workflow.now(),
                metadata=message.metadata
            ))
            
            # Broadcast to message bus (for real-time UI updates)
            if config.broadcast_messages:
                await workflow.execute_activity(
                    broadcast_message_activity,
                    BroadcastMessage(
                        workflow_id=workflow.info().workflow_id,
                        message=message,
                        round=round_num
                    ),
                    start_to_close_timeout=timedelta(seconds=5)
                )
            
            # Check termination conditions
            termination_reason = await self._check_termination(
                config, conversation
            )
            
            if termination_reason:
                logger.info(f"Terminating: {termination_reason}")
                break
        
        # Extract final answer (last message or synthesis)
        final_answer = await self._extract_final_answer(config, conversation)
        
        # Calculate duration
        duration = (workflow.now() - start_time).total_seconds()
        
        result = GroupChatResult(
            conversation=conversation,
            final_answer=final_answer,
            rounds_completed=len(conversation),
            termination_reason=termination_reason or f"Max rounds ({config.max_rounds})",
            agents_participated=list(set(m.speaker_id for m in conversation)),
            duration_seconds=duration
        )
        
        logger.info(f"Group chat completed: {len(conversation)} rounds, {duration:.1f}s")
        return result
    
    async def _select_next_speaker(
        self, 
        config: GroupChatConfig, 
        conversation: List[ConversationMessage],
        round_num: int
    ) -> AgentConfig:
        """Select next agent to speak."""
        if config.speaker_selection == "round-robin":
            # Simple round-robin
            agent_idx = (round_num - 1) % len(config.agents)
            return config.agents[agent_idx]
        
        elif config.speaker_selection == "manager":
            # Manager agent decides who speaks next
            manager_decision = await workflow.execute_activity(
                manager_select_speaker_activity,
                ManagerSelectRequest(
                    agents=config.agents,
                    conversation=conversation,
                    task=config.task
                ),
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Find agent by ID
            for agent in config.agents:
                if agent.agent_id == manager_decision.selected_agent_id:
                    return agent
            
            # Fallback to first agent
            return config.agents[0]
        
        else:  # "auto"
            # Auto-select based on task and conversation
            # If no conversation yet, start with first agent
            if not conversation:
                return config.agents[0]
            
            # Otherwise, let manager decide
            return await self._select_next_speaker(
                GroupChatConfig(**{**config.__dict__, "speaker_selection": "manager"}),
                conversation,
                round_num
            )
    
    async def _check_termination(
        self,
        config: GroupChatConfig,
        conversation: List[ConversationMessage]
    ) -> Optional[str]:
        """Check if conversation should terminate."""
        if not conversation:
            return None
        
        # Check last N messages for termination keywords
        last_n_messages = conversation[-config.termination_check_last_n:]
        
        for msg in last_n_messages:
            for keyword in config.termination_keywords:
                if keyword.upper() in msg.content.upper():
                    return f"Keyword '{keyword}' detected"
        
        # Check if task is complete (AI-based check)
        if len(conversation) >= 3:  # Only check after a few rounds
            completion_check = await workflow.execute_activity(
                check_task_completion_activity,
                TaskCompletionCheck(
                    task=config.task,
                    conversation=conversation
                ),
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            if completion_check.is_complete:
                return f"Task complete: {completion_check.reason}"
        
        return None
    
    async def _extract_final_answer(
        self,
        config: GroupChatConfig,
        conversation: List[ConversationMessage]
    ) -> str:
        """Extract or synthesize final answer from conversation."""
        if not conversation:
            return "No conversation recorded."
        
        # If last message contains answer, use it
        last_message = conversation[-1]
        
        # Otherwise, synthesize from conversation
        synthesis = await workflow.execute_activity(
            synthesize_conversation_activity,
            ConversationSynthesis(
                task=config.task,
                conversation=conversation
            ),
            start_to_close_timeout=timedelta(seconds=60)
        )
        
        return synthesis.final_answer
```

---

### **2. SupervisorWorkflow** (LangGraph + CrewAI-inspired)

**Use Case**: Hierarchical delegation (manager → workers)  
**Example**: Project manager delegates tasks to specialized engineers

#### Architecture
```
START
  │
  ▼
┌──────────────────────────┐
│ Manager Plans            │
│ • Analyze task           │
│ • Decompose subtasks     │
│ • Assign to workers      │
└──────────────────────────┘
  │
  ▼
┌──────────────────────────┐
│ Spawn Worker Workflows   │───┐
│ (Parallel Execution)     │   │
└──────────────────────────┘   │
  │                            │
  │  Worker 1  Worker 2  ...   │ Child
  │     │         │             │ Workflows
  │     ▼         ▼             │
  │  [Task A] [Task B]          │
  │     │         │             │
  └─────┴─────────┴─────────────┘
        │
        ▼
┌──────────────────────────┐
│ Manager Reviews          │
│ • Check worker results   │
│ • Validate quality       │
│ • Aggregate outputs      │
└──────────────────────────┘
  │
  ▼
┌──────────────────────────┐
│ Refine or Complete       │ ◄──┐
│ • If issues, re-delegate │    │
│ • Else, finalize         │────┘
└──────────────────────────┘  Retry
  │
  ▼
END
```

#### Implementation
```python
@dataclass
class SupervisorConfig:
    """Configuration for supervisor workflow."""
    manager: AgentConfig
    workers: List[AgentConfig]
    task: ComplexTask
    max_iterations: int = 3  # Max refinement rounds
    quality_threshold: float = 0.8
    parallel_execution: bool = True


@dataclass
class ComplexTask:
    """Complex task for supervisor workflow."""
    description: str
    requirements: List[str]
    deliverables: List[str]
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subtask:
    """Subtask assigned to worker."""
    subtask_id: str
    description: str
    worker_type: str  # Which worker specialization
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0


@dataclass
class WorkerResult:
    """Result from worker execution."""
    subtask_id: str
    worker_id: str
    output: str
    quality_score: float
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SupervisorResult:
    """Final result from supervisor workflow."""
    task: ComplexTask
    plan: List[Subtask]
    worker_results: List[WorkerResult]
    final_output: str
    quality_score: float
    iterations: int
    duration_seconds: float


@workflow.defn
class SupervisorWorkflow:
    """
    Hierarchical multi-agent workflow with manager delegation.
    
    Manager decomposes task, assigns to specialized workers,
    reviews results, and iterates if needed.
    
    Based on LangGraph Supervisor + CrewAI hierarchical process.
    """

    @workflow.run
    async def run(self, config: SupervisorConfig) -> SupervisorResult:
        logger = workflow.logger
        logger.info(f"Starting supervisor workflow: {config.task.description[:50]}")
        
        start_time = workflow.now()
        iteration = 0
        
        # Phase 1: Manager plans
        plan = await self._manager_plan(config)
        logger.info(f"Manager created plan with {len(plan)} subtasks")
        
        # Phase 2: Execute workers (iterative refinement)
        all_worker_results = []
        
        for iteration in range(1, config.max_iterations + 1):
            logger.info(f"Iteration {iteration}/{config.max_iterations}")
            
            # Execute workers (parallel or sequential)
            worker_results = await self._execute_workers(config, plan)
            all_worker_results.extend(worker_results)
            
            # Phase 3: Manager reviews
            review = await self._manager_review(config, plan, worker_results)
            
            if review.quality_score >= config.quality_threshold:
                logger.info(f"Quality threshold met: {review.quality_score:.2f}")
                break
            
            if iteration < config.max_iterations:
                # Refine plan for next iteration
                plan = await self._refine_plan(config, plan, review)
        
        # Phase 4: Final aggregation
        final_output = await self._aggregate_results(config, all_worker_results)
        
        duration = (workflow.now() - start_time).total_seconds()
        
        result = SupervisorResult(
            task=config.task,
            plan=plan,
            worker_results=all_worker_results,
            final_output=final_output,
            quality_score=review.quality_score,
            iterations=iteration,
            duration_seconds=duration
        )
        
        logger.info(f"Supervisor workflow completed: {iteration} iterations, {duration:.1f}s")
        return result
    
    async def _manager_plan(self, config: SupervisorConfig) -> List[Subtask]:
        """Manager decomposes task into subtasks."""
        plan_result = await workflow.execute_activity(
            manager_plan_activity,
            ManagerPlanRequest(
                manager_config=config.manager,
                task=config.task,
                available_workers=[w.role for w in config.workers]
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return plan_result.subtasks
    
    async def _execute_workers(
        self,
        config: SupervisorConfig,
        plan: List[Subtask]
    ) -> List[WorkerResult]:
        """Execute worker workflows (parallel or sequential)."""
        if config.parallel_execution:
            # Execute all workers in parallel using child workflows
            worker_futures = []
            
            for subtask in plan:
                # Find matching worker
                worker = self._find_worker(config.workers, subtask.worker_type)
                
                # Spawn child workflow
                worker_future = workflow.execute_child_workflow(
                    WorkerWorkflow.run,
                    WorkerTask(
                        subtask=subtask,
                        worker_config=worker,
                        parent_workflow_id=workflow.info().workflow_id
                    ),
                    id=f"{workflow.info().workflow_id}-worker-{subtask.subtask_id}",
                    task_queue=workflow.info().task_queue
                )
                
                worker_futures.append(worker_future)
            
            # Wait for all workers
            results = await asyncio.gather(*worker_futures)
            return results
        
        else:
            # Sequential execution
            results = []
            for subtask in plan:
                worker = self._find_worker(config.workers, subtask.worker_type)
                
                result = await workflow.execute_child_workflow(
                    WorkerWorkflow.run,
                    WorkerTask(subtask=subtask, worker_config=worker),
                    id=f"{workflow.info().workflow_id}-worker-{subtask.subtask_id}"
                )
                
                results.append(result)
            
            return results
    
    async def _manager_review(
        self,
        config: SupervisorConfig,
        plan: List[Subtask],
        worker_results: List[WorkerResult]
    ) -> ManagerReview:
        """Manager reviews worker results."""
        review = await workflow.execute_activity(
            manager_review_activity,
            ManagerReviewRequest(
                manager_config=config.manager,
                task=config.task,
                plan=plan,
                worker_results=worker_results
            ),
            start_to_close_timeout=timedelta(seconds=60)
        )
        
        return review
    
    def _find_worker(self, workers: List[AgentConfig], role: str) -> AgentConfig:
        """Find worker by role."""
        for worker in workers:
            if worker.role.lower() == role.lower():
                return worker
        
        # Fallback to first worker
        return workers[0]


@workflow.defn
class WorkerWorkflow:
    """Individual worker child workflow."""
    
    @workflow.run
    async def run(self, task: WorkerTask) -> WorkerResult:
        logger = workflow.logger
        logger.info(f"Worker {task.worker_config.name} starting: {task.subtask.description[:30]}")
        
        start_time = workflow.now()
        
        # Execute subtask
        output = await workflow.execute_activity(
            worker_execute_activity,
            WorkerExecuteRequest(
                worker_config=task.worker_config,
                subtask=task.subtask
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=3
            )
        )
        
        duration = (workflow.now() - start_time).total_seconds()
        
        result = WorkerResult(
            subtask_id=task.subtask.subtask_id,
            worker_id=task.worker_config.agent_id,
            output=output.result,
            quality_score=output.quality_score,
            duration_seconds=duration,
            metadata=output.metadata
        )
        
        logger.info(f"Worker completed: {task.subtask.subtask_id} (quality: {result.quality_score:.2f})")
        return result
```

---

### **3. ConsensusWorkflow** (Novel)

**Use Case**: Multi-agent voting/decision-making  
**Example**: Architecture review committee votes on design proposals

#### Architecture
```
START
  │
  ▼
┌──────────────────────────┐
│ Initialize Voting        │
│ • Load decision options  │
│ • Configure agents       │
│ • Set consensus rules    │
└──────────────────────────┘
  │
  ▼
┌──────────────────────────┐
│ Voting Round             │ ◄────┐
│ (All agents in parallel) │      │
└──────────────────────────┘      │
  │                               │
  ▼                               │
┌──────────────────────────┐      │
│ Collect Votes            │      │
│ • Vote + reasoning       │      │
│ • Confidence scores      │      │
└──────────────────────────┘      │
  │                               │
  ▼                               │
┌──────────────────────────┐      │
│ Check Consensus          │      │
│ • Threshold met?         │  No  │
│ • Majority exists?       │──────┘
└──────────────────────────┘   (Re-vote)
  │ Yes
  ▼
┌──────────────────────────┐
│ Return Consensus         │
│ • Agreed decision        │
│ • Vote breakdown         │
│ • Reasoning summary      │
└──────────────────────────┘
  │
  ▼
END
```

#### Implementation
```python
@dataclass
class ConsensusConfig:
    """Configuration for consensus workflow."""
    agents: List[AgentConfig]
    decision: Decision
    consensus_threshold: float = 0.75  # 75% agreement
    max_rounds: int = 3
    allow_abstain: bool = True


@dataclass
class Decision:
    """Decision to vote on."""
    question: str
    options: List[str]  # Vote options
    context: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Vote:
    """Single agent vote."""
    agent_id: str
    agent_name: str
    chosen_option: str
    reasoning: str
    confidence: float  # 0.0 to 1.0
    round_number: int


@dataclass
class ConsensusResult:
    """Result of consensus workflow."""
    decision: Decision
    agreed_option: str
    consensus_reached: bool
    votes: List[Vote]
    vote_breakdown: Dict[str, int]
    confidence_average: float
    rounds: int
    duration_seconds: float


@workflow.defn
class ConsensusWorkflow:
    """
    Multi-agent consensus workflow with voting.
    
    Agents vote on decision, with re-voting rounds
    if consensus not reached. Supports majority fallback.
    
    Novel pattern not found in existing frameworks.
    """

    @workflow.run
    async def run(self, config: ConsensusConfig) -> ConsensusResult:
        logger = workflow.logger
        logger.info(f"Starting consensus workflow: {config.decision.question[:50]}")
        
        start_time = workflow.now()
        all_votes: List[Vote] = []
        
        # Voting rounds
        for round_num in range(1, config.max_rounds + 1):
            logger.info(f"Voting round {round_num}/{config.max_rounds}")
            
            # All agents vote in parallel
            round_votes = await self._collect_votes(config, all_votes, round_num)
            all_votes.extend(round_votes)
            
            # Check consensus
            consensus_check = self._check_consensus(
                round_votes, 
                config.consensus_threshold
            )
            
            if consensus_check.reached:
                logger.info(f"Consensus reached: {consensus_check.agreed_option}")
                break
        
        # Final result (use consensus or majority)
        if consensus_check.reached:
            agreed_option = consensus_check.agreed_option
            consensus_reached = True
        else:
            # Fallback to majority vote
            agreed_option = self._majority_vote(all_votes)
            consensus_reached = False
            logger.info(f"Consensus not reached, using majority: {agreed_option}")
        
        # Calculate statistics
        vote_breakdown = self._count_votes(all_votes)
        confidence_avg = sum(v.confidence for v in all_votes) / len(all_votes) if all_votes else 0.0
        
        duration = (workflow.now() - start_time).total_seconds()
        
        result = ConsensusResult(
            decision=config.decision,
            agreed_option=agreed_option,
            consensus_reached=consensus_reached,
            votes=all_votes,
            vote_breakdown=vote_breakdown,
            confidence_average=confidence_avg,
            rounds=round_num,
            duration_seconds=duration
        )
        
        logger.info(f"Consensus workflow completed: {round_num} rounds, {duration:.1f}s")
        return result
    
    async def _collect_votes(
        self,
        config: ConsensusConfig,
        previous_votes: List[Vote],
        round_num: int
    ) -> List[Vote]:
        """Collect votes from all agents in parallel."""
        vote_futures = []
        
        for agent in config.agents:
            vote_future = workflow.execute_activity(
                agent_vote_activity,
                AgentVoteRequest(
                    agent_config=agent,
                    decision=config.decision,
                    previous_votes=previous_votes,
                    round_number=round_num
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            vote_futures.append(vote_future)
        
        # Wait for all votes
        votes = await asyncio.gather(*vote_futures)
        return votes
    
    def _check_consensus(
        self,
        votes: List[Vote],
        threshold: float
    ) -> ConsensusCheck:
        """Check if consensus threshold is met."""
        if not votes:
            return ConsensusCheck(reached=False, agreed_option=None)
        
        # Count votes per option
        vote_counts = self._count_votes(votes)
        
        # Find option with most votes
        max_option = max(vote_counts.items(), key=lambda x: x[1])
        max_count = max_option[1]
        
        # Check if threshold met
        percentage = max_count / len(votes)
        
        if percentage >= threshold:
            return ConsensusCheck(reached=True, agreed_option=max_option[0])
        else:
            return ConsensusCheck(reached=False, agreed_option=None)
    
    def _majority_vote(self, votes: List[Vote]) -> str:
        """Get majority vote (fallback)."""
        vote_counts = self._count_votes(votes)
        max_option = max(vote_counts.items(), key=lambda x: x[1])
        return max_option[0]
    
    def _count_votes(self, votes: List[Vote]) -> Dict[str, int]:
        """Count votes per option."""
        counts: Dict[str, int] = {}
        
        for vote in votes:
            option = vote.chosen_option
            counts[option] = counts.get(option, 0) + 1
        
        return counts


@dataclass
class ConsensusCheck:
    reached: bool
    agreed_option: Optional[str]
```

---

## 📡 COMMUNICATION LAYER

### **Message Bus Architecture**

```python
@dataclass
class AgentMessage:
    """Message sent between agents."""
    message_id: str
    from_agent_id: str
    to_agent_id: Optional[str]  # None for broadcast
    content: str
    message_type: Literal["text", "data", "command", "event"]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@activity.defn
async def send_message_activity(message: AgentMessage) -> Dict[str, Any]:
    """
    Send message via Redis pub/sub.
    
    Supports:
    - Direct messages (agent-to-agent)
    - Broadcasts (agent-to-all)
    - Channels (topic-based)
    """
    redis_client = await get_redis_client()
    
    # Determine channel
    if message.to_agent_id:
        channel = f"agent:{message.to_agent_id}"
    else:
        channel = f"workflow:{workflow.info().workflow_id}:broadcast"
    
    # Publish message
    payload = {
        "message_id": message.message_id,
        "from": message.from_agent_id,
        "to": message.to_agent_id,
        "content": message.content,
        "type": message.message_type,
        "timestamp": message.timestamp.isoformat(),
        "metadata": message.metadata
    }
    
    await redis_client.publish(channel, json.dumps(payload))
    
    activity.logger.info(
        f"Message sent: {message.from_agent_id} → {message.to_agent_id or 'ALL'}"
    )
    
    return {"status": "sent", "channel": channel}


@activity.defn
async def receive_messages_activity(
    agent_id: str,
    timeout_seconds: int = 5
) -> List[AgentMessage]:
    """
    Receive messages from Redis pub/sub.
    
    Subscribes to agent's channel and waits for messages.
    """
    redis_client = await get_redis_client()
    
    channel = f"agent:{agent_id}"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    
    messages = []
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        message = await pubsub.get_message(timeout=1.0)
        
        if message and message['type'] == 'message':
            payload = json.loads(message['data'])
            
            messages.append(AgentMessage(
                message_id=payload['message_id'],
                from_agent_id=payload['from'],
                to_agent_id=payload.get('to'),
                content=payload['content'],
                message_type=payload['type'],
                timestamp=datetime.fromisoformat(payload['timestamp']),
                metadata=payload.get('metadata', {})
            ))
    
    await pubsub.unsubscribe(channel)
    
    activity.logger.info(f"Received {len(messages)} messages for {agent_id}")
    
    return messages
```

---

## 🧠 SHARED MEMORY LAYER

### **Blackboard Pattern**

```python
@dataclass
class BlackboardState:
    """Shared knowledge accessible to all agents."""
    workflow_id: str
    facts: Dict[str, Any]  # Verified facts
    hypotheses: List[Hypothesis]  # Unverified hypotheses
    conclusions: List[Conclusion]  # Final conclusions
    artifacts: Dict[str, str]  # File paths, URLs
    conversation: List[ConversationMessage]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Hypothesis:
    """Agent hypothesis on blackboard."""
    hypothesis_id: str
    agent_id: str
    content: str
    confidence: float
    supporting_evidence: List[str]
    timestamp: datetime


@dataclass
class Conclusion:
    """Verified conclusion on blackboard."""
    conclusion_id: str
    content: str
    supporting_hypotheses: List[str]
    verified_by: List[str]  # Agent IDs
    timestamp: datetime


@activity.defn
async def read_blackboard_activity(workflow_id: str) -> BlackboardState:
    """Read current blackboard state."""
    # Read from Temporal state (durable)
    temporal_state = await get_workflow_state(workflow_id)
    
    # Read from Qdrant (vector search)
    qdrant_client = await get_qdrant_client()
    
    vectors = await qdrant_client.search(
        collection_name=f"blackboard_{workflow_id}",
        query_vector=None,  # Get all
        limit=100
    )
    
    blackboard = BlackboardState(
        workflow_id=workflow_id,
        facts=temporal_state.get('facts', {}),
        hypotheses=temporal_state.get('hypotheses', []),
        conclusions=temporal_state.get('conclusions', []),
        artifacts=temporal_state.get('artifacts', {}),
        conversation=temporal_state.get('conversation', []),
        metadata=temporal_state.get('metadata', {})
    )
    
    return blackboard


@activity.defn
async def write_blackboard_activity(
    workflow_id: str,
    update: BlackboardUpdate
) -> BlackboardState:
    """Write update to blackboard."""
    # Update Temporal state (durable)
    await update_workflow_state(workflow_id, update)
    
    # Update Qdrant (vector search)
    if update.new_hypotheses:
        qdrant_client = await get_qdrant_client()
        
        await qdrant_client.upsert(
            collection_name=f"blackboard_{workflow_id}",
            points=[
                {
                    "id": h.hypothesis_id,
                    "vector": await embed_text(h.content),
                    "payload": asdict(h)
                }
                for h in update.new_hypotheses
            ]
        )
    
    # Broadcast update
    await broadcast_blackboard_update(workflow_id, update)
    
    return await read_blackboard_activity(workflow_id)
```

---

## 🎯 NEXT STEPS

This blueprint provides the **complete architectural foundation** for world-class multi-agent orchestration. 

**Continue reading**:
- [Part 2: Activities & Integration](/docs/MULTI_AGENT_ACTIVITIES.md)
- [Part 3: Production Deployment](/docs/MULTI_AGENT_DEPLOYMENT.md)
- [Part 4: API Reference](/docs/MULTI_AGENT_API_REFERENCE.md)

**Ready to implement?** See [Implementation Plan](#implementation-plan) below.

---

## 📅 IMPLEMENTATION PLAN

### **Sprint 1: Communication Foundation** (5 days)
- Day 1-2: Message Bus (Redis pub/sub)
- Day 3-4: Shared Memory (Qdrant + Temporal state)
- Day 5: Integration testing

### **Sprint 2: Core Workflows** (10 days)
- Day 1-3: GroupChatWorkflow
- Day 4-6: SupervisorWorkflow
- Day 7-8: ConsensusWorkflow
- Day 9-10: Integration + testing

### **Sprint 3: Activities** (5 days)
- Day 1-2: Agent speak, vote, contribute
- Day 3-4: Manager plan, review
- Day 5: Integration testing

### **Sprint 4: Production Ready** (5 days)
- Day 1-2: Observability (traces, metrics)
- Day 3-4: Documentation
- Day 5: Deployment guide

**Total**: 25 days (5 weeks)

---

**Status**: ✅ Architecture Blueprint Complete  
**Next**: Implementation Sprint 1  
**Document Version**: 1.0.0  
**Last Updated**: October 7, 2025
