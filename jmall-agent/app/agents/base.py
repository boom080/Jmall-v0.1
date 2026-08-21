"""Base class for all agents in the multi-agent orchestration system."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.llm.cost_tracker import CostTracker
from app.llm.router import LLMRouter
from app.providers.factory import ProviderFactory

logger = logging.getLogger(__name__)

# Max tool calling iterations to prevent infinite loops
DEFAULT_MAX_TOOL_ITERATIONS = 3


class BaseAgent(ABC):
    """Base class for all agents.

    Each agent has:
    - agent_type: A unique identifier (e.g., "market_research")
    - system_prompt: The system prompt for the LLM
    - tools: Optional list of OpenAI-compatible tool definitions
    - model_preference: Cost tier preference ("cheap", "medium", "strong")
    """

    agent_type: str = "base"
    system_prompt: str = "You are a helpful AI assistant."
    tools: List[Dict[str, Any]] = []
    model_preference: str = "medium"

    def __init__(
        self,
        settings: Settings,
        provider_factory: ProviderFactory,
        llm_router: LLMRouter,
        cost_tracker: Optional[CostTracker] = None,
    ) -> None:
        self.settings = settings
        self.provider_factory = provider_factory
        self.llm_router = llm_router
        self.cost_tracker = cost_tracker

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task.

        Args:
            state: The current orchestration state dict

        Returns:
            Updated state dict with this agent's results
        """
        ...

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return self.system_prompt

    def _call_llm(
        self,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        extra_messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Call the LLM with the agent's system prompt and user message.

        Args:
            user_message: The user/content message to send
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            extra_messages: Additional messages to include

        Returns:
            Dict with: content, input_tokens, output_tokens, provider, model, success, error
        """
        provider_name, model_name = self.llm_router.route(self.agent_type)

        messages = [{"role": "system", "content": self.system_prompt}]
        if extra_messages:
            messages.extend(extra_messages)
        messages.append({"role": "user", "content": user_message})

        logger.info(
            "Agent '%s' calling LLM: provider=%s model=%s",
            self.agent_type, provider_name, model_name,
        )

        result = self.provider_factory.chat(
            provider_name=provider_name,
            model_name=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not result.get("success", False):
            raise RuntimeError(
                f"LLM provider {provider_name}/{model_name} failed: "
                f"{result.get('error') or 'unknown error'}"
            )

        # Track cost
        if self.cost_tracker:
            self.cost_tracker.track(
                provider=result.get("provider", provider_name),
                model=result.get("model", model_name),
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                agent_type=self.agent_type,
            )

        return result

    async def _call_llm_with_tools(
        self,
        user_message: str,
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_iterations: int = DEFAULT_MAX_TOOL_ITERATIONS,
        extra_messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Call LLM with tool definitions, handling the tool calling loop.

        Implements the agentic pattern:
        1. Send system + user + tools to LLM
        2. If LLM returns tool_calls → execute tools → send results back → repeat
        3. If LLM returns content → return final result

        Args:
            user_message: The user/content message to send
            tools: OpenAI-compatible tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum output tokens per call
            max_iterations: Maximum tool calling rounds (prevents infinite loops)
            extra_messages: Additional messages to include

        Returns:
            Dict with: content, input_tokens, output_tokens, provider, model,
            success, error, tool_call_history
        """
        provider_name, model_name = self.llm_router.route(self.agent_type)

        # Build conversation messages
        messages: List[Dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]
        if extra_messages:
            messages.extend(extra_messages)
        messages.append({"role": "user", "content": user_message})

        total_input_tokens = 0
        total_output_tokens = 0
        tool_call_history: List[Dict[str, Any]] = []

        for iteration in range(max_iterations + 1):
            logger.info(
                "Agent '%s' tool-calling round %d: provider=%s model=%s",
                self.agent_type, iteration, provider_name, model_name,
            )

            result = self.provider_factory.chat(
                provider_name=provider_name,
                model_name=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools if iteration < max_iterations else None,
                tool_choice="auto" if iteration < max_iterations else "none",
            )

            if not result.get("success", False):
                raise RuntimeError(
                    f"LLM provider {provider_name}/{model_name} failed: "
                    f"{result.get('error') or 'unknown error'}"
                )

            total_input_tokens += result.get("input_tokens", 0)
            total_output_tokens += result.get("output_tokens", 0)

            tool_calls = result.get("tool_calls")
            content = result.get("content")

            if tool_calls:
                # LLM wants to call tools
                logger.info(
                    "Agent '%s' tool calls: %s",
                    self.agent_type,
                    [tc.get("function", {}).get("name", "unknown") for tc in tool_calls],
                )

                # Append assistant message with tool_calls
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls,
                })

                # Execute each tool and append results
                for tc in tool_calls:
                    tool_name = tc.get("function", {}).get("name", "")
                    tool_id = tc.get("id", "")
                    try:
                        tool_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                    except json.JSONDecodeError:
                        tool_args = {}

                    tool_start = {}
                    try:
                        tool_result = await self._execute_tool(tool_name, tool_args)
                        tool_start = {
                            "name": tool_name,
                            "arguments": tool_args,
                            "success": True,
                            "result_preview": str(tool_result)[:200],
                        }
                        provider = getattr(tool_result, "provider", "")
                        sources = getattr(tool_result, "sources", None)
                        if provider:
                            tool_start["provider"] = provider
                        if sources:
                            tool_start["sources"] = sources
                        tool_input_tokens = int(getattr(tool_result, "input_tokens", 0) or 0)
                        tool_output_tokens = int(getattr(tool_result, "output_tokens", 0) or 0)
                        if tool_input_tokens or tool_output_tokens:
                            tool_start["usage"] = {
                                "model": getattr(tool_result, "model", ""),
                                "input_tokens": tool_input_tokens,
                                "output_tokens": tool_output_tokens,
                                "total_tokens": tool_input_tokens + tool_output_tokens,
                            }
                            if self.cost_tracker:
                                self.cost_tracker.track(
                                    provider=provider or "search",
                                    model=getattr(tool_result, "model", "") or "unknown_search_model",
                                    input_tokens=tool_input_tokens,
                                    output_tokens=tool_output_tokens,
                                    agent_type=f"{self.agent_type}.web_search",
                                )
                    except Exception as exc:
                        logger.error(
                            "Tool '%s' execution failed: %s", tool_name, exc,
                        )
                        tool_result = f"工具执行失败: {exc}"
                        tool_start = {
                            "name": tool_name,
                            "arguments": tool_args,
                            "success": False,
                            "error": str(exc),
                        }

                    tool_call_history.append(tool_start)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": str(tool_result),
                    })

                # Continue loop to get LLM's next response
                continue

            # No tool_calls — this is the final answer
            if content:
                break

            # Neither content nor tool_calls — force stop
            logger.warning(
                "Agent '%s': no content or tool_calls in round %d, stopping",
                self.agent_type, iteration,
            )
            result["content"] = ""
            break

        # Track total cost
        if self.cost_tracker:
            self.cost_tracker.track(
                provider=result.get("provider", provider_name),
                model=result.get("model", model_name),
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                agent_type=self.agent_type,
            )

        # Preserve final result fields
        return {
            "content": result.get("content", ""),
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "provider": result.get("provider", provider_name),
            "model": result.get("model", model_name),
            "success": result.get("success", True),
            "error": result.get("error"),
            "tool_call_history": tool_call_history,
            "http_status": result.get("http_status"),
            "duration_ms": result.get("duration_ms", 0),
            "retry_count": result.get("retry_count", 0),
        }

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name and return the result string.

        Override this in subclasses to provide actual tool implementations.
        The default implementation raises NotImplementedError.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments parsed from the LLM's tool_call

        Returns:
            Tool result as a string (will be sent back to the LLM)
        """
        raise NotImplementedError(
            f"Agent '{self.agent_type}' does not implement tool '{tool_name}'. "
            f"Override _execute_tool() to handle tool execution."
        )

    def _parse_json_response(self, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """Try to parse JSON from LLM response content.

        Args:
            llm_result: Result dict from _call_llm

        Returns:
            Parsed JSON dict, or dict with raw content on failure
        """
        content = llm_result.get("content", "")
        if not content:
            return {"raw_content": "", "parse_error": "Empty response"}

        # Try direct JSON parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                try:
                    return json.loads(content[start:end].strip())
                except json.JSONDecodeError:
                    pass
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                try:
                    return json.loads(content[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try extracting JSON between braces
        brace_start = content.find("{")
        brace_end = content.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            try:
                return json.loads(content[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass

        # Return raw content
        return {"raw_content": content, "parse_error": "Could not parse JSON from response"}

    def _make_state_update(self, key: str, value: Any) -> Dict[str, Any]:
        """Create a state update dict."""
        return {key: value}
