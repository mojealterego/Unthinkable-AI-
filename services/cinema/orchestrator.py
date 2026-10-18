from __future__ import annotations

import os
from typing import Any

from services.cinema.models import StudioSyncResult
from services.cinema.demo_data import demo_result

try:
    from google.adk.agents import LlmAgent, ParallelAgent
except Exception:  # Optional for deterministic local demo/tests.
    LlmAgent = ParallelAgent = None

try:
    from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
except Exception:
    McpToolset = None
    StreamableHTTPConnectionParams = None

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _configured() -> bool:
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("CLICKHOUSE_MCP_URL"))


def _mcp_toolset():
    url = os.getenv("CLICKHOUSE_MCP_URL")
    token = os.getenv("CLICKHOUSE_MCP_AUTH_TOKEN")
    if not url or McpToolset is None or StreamableHTTPConnectionParams is None:
        return None
    headers = {"Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=url, headers=headers)
    )


def build_agent_graph():
    """Build the real ADK graph used by the configured deployment."""
    if LlmAgent is None or ParallelAgent is None:
        raise RuntimeError("google-adk is not installed")

    toolset = _mcp_toolset()
    if toolset is None:
        raise RuntimeError("CLICKHOUSE_MCP_URL is not configured for the live graph")

    scenario_agent = LlmAgent(
        name="ScenarioImpactAgent",
        model=MODEL,
        instruction=(
            "Identify operational consequences of the production incident. "
            "Return concise structured findings and never invent contractual facts."
        ),
    )
    logistics_agent = LlmAgent(
        name="LocationLogisticsAgent",
        model=MODEL,
        instruction=(
            "Evaluate location and logistics recovery options. Rank them by schedule feasibility, "
            "operational fit and cost evidence. Distinguish facts from estimates."
        ),
    )
    financial_agent = LlmAgent(
        name="FinancialRiskAgent",
        model=MODEL,
        tools=[toolset],
        instruction=(
            "Quantify production budget deltas using the ClickHouse MCP tools when data is available. "
            "Use read-only analytics only. Never perform writes. Cite retrieved values as MCP evidence "
            "and label model-derived estimates separately."
        ),
    )
    parallel = ParallelAgent(
        name="ProductionAnalysisParallel",
        sub_agents=[scenario_agent, logistics_agent, financial_agent],
    )
    return LlmAgent(
        name="StudioSyncCoordinator",
        model=MODEL,
        instruction=(
            "Act as the production operations lead. Coordinate the specialist analyses, reconcile conflicts, "
            "rank recovery options, identify approval requirements and produce an auditable decision brief. "
            "Never claim an external action was executed unless a tool explicitly confirms execution."
        ),
        sub_agents=[parallel],
    )


def run_studiosync(instruction: str, mode: str | None = None) -> dict[str, Any]:
    """Run deterministic demo by default; never silently fake live execution."""
    requested = (mode or os.getenv("STUDIOSYNC_MODE", "demo")).lower()
    if requested not in {"demo", "live"}:
        raise ValueError("mode must be 'demo' or 'live'")

    configured = _configured()
    if requested == "live":
        if not configured:
            raise RuntimeError(
                "Live mode requires GOOGLE_CLOUD_PROJECT and CLICKHOUSE_MCP_URL. "
                "Use mode=demo for reproducible evaluation without cloud credentials."
            )
        # Graph construction is intentionally explicit. A deployed runner can call the ADK
        # runtime/session service here; the API never falls back to synthetic data silently.
        build_agent_graph()
        raise RuntimeError(
            "Live graph is configured. Connect it to the selected ADK runner/session service "
            "for deployment-specific execution; no synthetic result is returned in live mode."
        )

    return demo_result(instruction, configured=configured).model_dump()
