"""AutoGen integration for group-chat style multi-agent conversations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

from temporalio import activity


@dataclass(slots=True)
class AgentConfig:
    """Validated configuration for each AutoGen agent."""

    name: str
    model: str
    system_message: str = ""
    llm_config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AgentConfig":
        try:
            name = str(payload["name"]).strip()
            model = str(payload.get("model", "gpt-4o-mini")).strip()
        except KeyError as exc:  # pragma: no cover - validated in tests
            raise ValueError(f"agent config missing required field: {exc.args[0]}") from exc

        if not name:
            raise ValueError("agent name cannot be empty")
        if not model:
            raise ValueError("model cannot be empty")

        return cls(
            name=name,
            model=model,
            system_message=str(payload.get("system_message", "")),
            llm_config=payload.get("llm_config"),
        )


def _get_autogen_components():
    try:  # pragma: no cover - exercised in runtime environment
        from autogen import AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "AutoGen is not installed. Add `pyautogen` to service dependencies before "
            "scheduling the `autogen-group-chat` activity."
        ) from exc

    return AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent


def _build_llm_config(agent: AgentConfig, default_temperature: float) -> Dict[str, Any]:
    if agent.llm_config:
        return agent.llm_config
    return {
        "config_list": [
            {
                "model": agent.model,
            }
        ],
        "temperature": default_temperature,
    }


def _termination_predicate(keywords: Iterable[str]):
    lowered = [kw.lower() for kw in keywords if kw]

    def _is_termination(message: Dict[str, Any]) -> bool:
        if not lowered:
            return False
        content = message.get("content") or ""
        return any(keyword in content.lower() for keyword in lowered)

    return _is_termination


def _serialize_conversation(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for msg in messages:
        serialized.append(
            {
                "speaker": msg.get("name") or msg.get("role", "unknown"),
                "role": msg.get("role", "assistant"),
                "content": msg.get("content", ""),
                "metadata": {
                    "thought": msg.get("thought"),
                    "summary": msg.get("summary"),
                },
            }
        )
    return serialized



@activity.defn(name="autogen-group-chat")
async def run_autogen_group_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a group-chat AutoGen conversation under Temporal control."""

    agents = payload.get("agents")
    task = payload.get("task")
    tenant = payload.get("tenant", "default")
    metadata = payload.get("metadata")
    max_rounds = int(payload.get("max_rounds", 20))
    temperature = float(payload.get("temperature", 0.7))
    termination_keywords = payload.get("termination_keywords")

    logger = activity.logger
    if agents is None:
        raise ValueError("at least one agent configuration is required")
    if task is None:
        raise ValueError("task description is required")

    logger.info(
        "Starting AutoGen group chat",
        extra={
            "tenant": tenant,
            "agent_count": len(agents),
            "max_rounds": max_rounds,
        },
    )

    if not agents:
        raise ValueError("at least one agent configuration is required")
    if max_rounds <= 0:
        raise ValueError("max_rounds must be positive")

    agent_configs = [AgentConfig.from_dict(agent) for agent in agents]

    AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent = _get_autogen_components()

    # Instantiate AutoGen agents using supplied configuration.
    autogen_agents: List[AssistantAgent] = []
    for config in agent_configs:
        llm_config = _build_llm_config(config, default_temperature=temperature)
        autogen_agents.append(
            AssistantAgent(
                name=config.name,
                system_message=config.system_message,
                llm_config=llm_config,
            )
        )

    term_keywords = termination_keywords or ["TERMINATE", "DONE"]
    user_proxy = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        is_termination_msg=_termination_predicate(term_keywords),
        max_consecutive_auto_reply=0,
    )

    groupchat = GroupChat(agents=[user_proxy, *autogen_agents], messages=[], max_round=max_rounds)
    manager = GroupChatManager(groupchat=groupchat)

    try:
        user_proxy.initiate_chat(manager, message=task)
    except Exception as exc:  # pragma: no cover - AutoGen raises custom errors
        logger.exception("AutoGen conversation failed")
        raise RuntimeError(f"autogen group chat failed: {exc}") from exc

    conversation = _serialize_conversation(groupchat.messages)

    logger.info(
        "AutoGen group chat completed",
        extra={
            "tenant": tenant,
            "turns": len(conversation),
            "agents": [config.name for config in agent_configs],
        },
    )

    return {
        "framework": "autogen",
        "pattern": "group_chat",
        "tenant": tenant,
        "metadata": metadata or {},
        "agents": [asdict(config) for config in agent_configs],
        "conversation": conversation,
        "turns": len(conversation),
    }
