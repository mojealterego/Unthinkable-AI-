# Cinematic Agents source provenance
Source: https://github.com/mojealterego/Cinematic-Agents (read-only inspection of main). Included the original `src/cinematic_agents/orchestrator.py` and `models.py` under a namespaced `services/cinema/crew` folder. Repo tree did not expose standalone LICENSE at inspection; confirm authorship/upstream permissions before external distribution.

`build_run` constructs an 18-role sequential production plan and sets `quality_gate=not_started`. It **does not** invoke models, synthesize video or approve release. Backend endpoint `POST /api/cinema/crew` requires API_KEY and returns `planning_only`.
