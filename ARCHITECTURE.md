# EcoScope AI 2.0 architecture

## Evidence before interpretation

The Streamlit action `Run environmental analysis` invokes the existing Python
science functions in `environment.py`. Each module returns metrics, tables,
computed facts, limitations and source records, or a visible unavailable result.
The user can generate standard reports without a language-model connection.

The separate `Run five-agent review` action creates a snapshot of this saved run.
The agents use the same underlying evidence. This design adds tool-using AI
interpretation while preserving reproducible environmental calculations.
Execution runs in a worker; progress events pass through a queue to the Streamlit
script thread, which owns all UI updates.

## Exactly five agents and a sequential process

`crew_workflow.build_crew()` constructs a CrewAI `Process.sequential` crew with
five agents and five synchronous tasks. Only the five files under `agents/`
define individual roles. `agent_common.py` supplies a shared constructor.

| Task | Agent | Explicit upstream context |
|---|---|---|
| 1 | Study coordinator | Study scope, available source IDs and computed checks |
| 2 | Climate and air analyst | Coordinator note and climate/air/outlook evidence |
| 3 | Geospatial and water analyst | Coordinator note and satellite/earthquake evidence |
| 4 | Ecology and field analyst | Coordinator note and biodiversity/field evidence |
| 5 | Evidence reviewer and report writer | All four completed notes and computed checks |

The coordinator is an ordinary first-stage agent, not a CrewAI hierarchical
manager. Automatic planning and delegation are disabled. This prevents extra
manager/planner model calls and keeps the number of agents at five.

Each agent chooses whether to call its three scoped tools through CrewAI's ReAct
executor. The reviewer can request all saved domains; each specialist can access
only its assigned domains. Tools do not fetch external URLs or execute arbitrary code.

| Tool | Behaviour |
|---|---|
| `read_evidence` | Facts, metrics, provenance, limitations and table/column inventory |
| `table_statistics` | Validated numeric mean, median, min, max, count or permitted sum |
| `quality_checks` | Deterministic coverage, scope and missing-evidence checks |

Only precipitation totals and record-count columns support sums. Missing numeric
values are unavailable, not zero. The tool reports valid and total row counts.

## Runtime and limits

- CrewAI is pinned to 1.15.22; Python 3.12 is the tested runtime.
- `GroqEvidenceLLM` implements CrewAI's `BaseLLM`. It sends plain role/content
  messages directly to Groq's fixed chat-completions endpoint.
- No LiteLLM dependency or prompt-cache extension fields are required.
- There is one per-run request/time budget and conservative pacing per key/model
  digest inside a server process. Default estimated token budget: 6,000 per minute.
- Maximum 18 model requests, three executor iterations per agent, one citation
  guardrail retry, 1,800 maximum completion tokens per request and a 600-second
  run budget. Network requests have separate bounded timeouts. An in-flight
  request can finish after the overall deadline; no later request is started.
- A provider error stops further model requests. Completed agent notes remain
  downloadable. No partial final briefing is labelled complete.
- Free-tier limits vary by account and model. Character-based token estimates
  are conservative heuristics and cannot guarantee avoidance of provider limits.

## Privacy and session handling

The real API key stays on its adapter instance and is excluded from serialization
and reports. Keys entered in the UI remain in that Streamlit session; a key in
Secrets is shared application configuration. A digest is used solely for pacing.
The LLM receives the question, local study metadata, summaries and requested
statistics. It does not receive raw raster pixels or uploaded file bytes.

CrewAI telemetry, tracing, memory and cache are disabled. `SessionCrew` replaces
the default latest-task SQLite output handler with a no-op handler; Streamlit
session state owns the completed notes. This private extension point is tested
against the pinned framework version. Re-test it before upgrading CrewAI.

There is no cross-session conversation memory, persistent checkpoint, background
job recovery or durable user project database. Download results before closing
the session. Standard public-data API caching is independent of AI session state.

## Evidence validation and reports

Source-ID guardrails reject unknown bracketed IDs and require a citation in a
final review when sources exist. They check citation structure and length, not
the truth of every sentence. Prompts also require uncertainty and explicitly
separate forecasts, reanalysis, observations and uncalibrated water proxies.

A SHA-256 fingerprint covers study settings, errors, source records, facts,
metrics, notes and full table contents. The review stores this fingerprint.
The app and export functions reject an incomplete or stale review. Raster bytes
are excluded because these agents work from numerical summaries and do not
visually inspect map images.

When selected, the completed review is an identified section in PDF and HTML.
The ZIP also contains the final Markdown and the five completed notes/activity
as JSON. Activity records stages, request counts and tool names; it does not
publish private model deliberation. All normal data/GIS exports remain available.

## Production boundary

This is a session-based Streamlit MVP. A production deployment needs durable jobs
and evidence storage, authentication, per-user/provider quotas, monitoring and
regional scientific validation. A five-agent review is not a calibrated hazard
model, an emergency warning, or independent peer review.
