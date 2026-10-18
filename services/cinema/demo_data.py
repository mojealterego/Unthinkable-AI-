from services.cinema.models import (
    Approval,
    BudgetDelta,
    Evidence,
    IntegrationStatus,
    ScenarioChange,
    StudioOption,
    StudioSyncResult,
)


def demo_result(instruction: str, configured: bool = False) -> StudioSyncResult:
    """Reproducible judging fixture. Values are explicitly synthetic."""
    return StudioSyncResult(
        incident_summary=(
            "Storm-driven cancellation of Scene 42. The recovery loop evaluates schedule, "
            "location, logistics and budget consequences before human approval."
        ),
        scenario_changes=[
            ScenarioChange(
                scene_id="42",
                change="Exterior shoot cancelled due to severe weather",
                operational_effects=[
                    "Move production into a controlled interior location",
                    "Re-check crew and cast windows",
                    "Recalculate overtime, location and transport costs",
                ],
            )
        ],
        studio_options=[
            StudioOption(
                name="Studio B",
                available_window="Next 24h",
                fit_score=0.93,
                estimated_cost=18000,
                notes="Best operational fit; minimal set rebuild.",
                evidence=["synthetic availability fixture", "synthetic cost fixture"],
            ),
            StudioOption(
                name="Warehouse 42",
                available_window="24–48h",
                fit_score=0.81,
                estimated_cost=12500,
                notes="Lower venue cost; higher art-department conversion effort.",
                evidence=["synthetic availability fixture", "synthetic cost fixture"],
            ),
            StudioOption(
                name="Stage C",
                available_window="36–48h",
                fit_score=0.74,
                estimated_cost=21000,
                notes="Strong capacity; adds transport complexity.",
                evidence=["synthetic availability fixture", "synthetic cost fixture"],
            ),
        ],
        budget=BudgetDelta(
            baseline=150000,
            revised=174000,
            delta=24000,
            confidence="medium",
        ),
        approvals=Approval(
            status="required",
            actions=[
                "Approve selected location",
                "Approve revised cost ceiling",
                "Approve any overtime or contractual change",
                "Release updated call sheet after approval",
            ],
        ),
        provenance=[
            Evidence(
                source="embedded_demo_fixture",
                type="synthetic",
                statement="All numeric location and budget values in demo mode are synthetic and reproducible.",
            ),
            Evidence(
                source="user_instruction",
                type="user_input",
                statement=f"Incident supplied by the user: {instruction}",
            ),
            Evidence(
                source="agent_graph",
                type="model_inference",
                statement="The configured runtime uses specialist agents for scenario, logistics and finance analysis.",
            ),
            Evidence(
                source="clickhouse_design_reference",
                type="synthetic",
                statement=(
                    "In configured mode, the financial specialist is grounded through the configured ClickHouse MCP endpoint; "
                    "no live query result is claimed in demo mode."
                ),
            ),
        ],
        integration=IntegrationStatus(
            mode="configured" if configured else "demo",
            gemini_configured=bool(configured),
            clickhouse_mcp_configured=bool(configured),
        ),
        next_step="Human review required before any consequential production decision.",
    )
