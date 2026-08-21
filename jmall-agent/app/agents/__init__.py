"""Agents module for the multi-agent orchestration system.

Each agent specializes in a specific task:
- OrchestratorAgent: Task decomposition and coordination
- MarketResearchAgent: Web search for market trends
- CopywriterAgent: E-commerce copy generation
- ReviewerAgent: Compliance and quality review
- StyleAdapterAgent: Platform-specific style adaptation
"""

from app.agents.base import BaseAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.market_research import MarketResearchAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.style_adapter import StyleAdapterAgent

__all__ = [
    "BaseAgent",
    "OrchestratorAgent",
    "MarketResearchAgent",
    "CopywriterAgent",
    "ReviewerAgent",
    "StyleAdapterAgent",
]
