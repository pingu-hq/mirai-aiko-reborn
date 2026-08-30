- Install/update dependencies with `uv sync` (this repo is `uv`-managed; Dockerfile also runs `uv sync --frozen`).
- Start the API with `uv run python main.py` (FastAPI app is built in `main.py`, and the container entrypoint uses `uvicorn main:app`).
- Ensure `secrets/.env` exists (settings are loaded from `app/core/local_config.py`); missing required keys will fail on first use (notably: `MONGO_DATABASE`, `GROQ_API_KEY`, `COHERE_API_KEY`, `MILVUS_URI`, `MILVUS_TOKEN`, `IS_DEVELOPMENT_MODE`).
- Redis auth is hardcoded to `127.0.0.1:6379` in `app/repositories/in_memory_database/redis_repository.py` (no `REDIS_URI` wiring exists).
- The endpoints use opaque-token cookie auth (`get_opaque_auth_service`) with cookie names `access` and `refresh` (opaque tokens stored in Redis; access TTL=5 minutes, refresh TTL=15 days; refresh can rotate cookies).
- Cookie `secure` flag depends on `IS_DEVELOPMENT_MODE` (`OpaqueAuthService.secure` returns `False` in development mode, otherwise `True`).
- FastAPI startup must run `app/core/lifespan.py` (it initializes Redis/Mongo/Milvus clients, httpx clients, CrewAI LLM cache, YAML/TOML prompt loading, and in-memory caches); run the server normally instead of importing routers ad-hoc.
- Real “chat workflow” wiring is in `POST /api/playground/ask-chat-sample-1` (it calls `MiraiAikoWorkflow`); `POST /api/chat/ask-chat` is a placeholder that always returns `{"crewai_result": "Null"}`.
- `MiraiAikoWorkflow.final_output` is incomplete (it calls `self._lily_tools.gpt_oss_120b()` without `await`/return), so expect placeholder/buggy responses while the workflow is being wired up.
- Prompt/config files are not arbitrary: Lily prompt templates are in `app/core/agents/config/chat_prompts.toml` (loaded/initialized in `lifespan` via `ConfigLoader.init_config_toml_file()`), and YAML prompts come from `chat_prompts.yaml` (cached via `lru_cache`).
- CrewAI agent/task definitions are limited to the whitelisted YAML names in `app/core/agents/agent_loader.py` (`agents.yaml`, `tasks.yaml`, `sample_agents.yaml`, `sample_tasks.yaml`); adding new YAML filenames won’t load.
- Config loading is cached (`lru_cache` / static fields), so after editing YAML/TOML configs you must restart the server to pick up changes.
- The repository no longer uses NATS, SSE, or a separate frontend directory; the FastAPI routes under `app/routers/*` provide the API, and a simple HTMX-based UI can be served as static files if desired.
- The Celery worker scaffold remains in `worker/main.py` but is not required for the current setup; all heavy work runs inside FastAPI as an async task.
- Run the API with `uv run python main.py`; no separate Celery process is needed.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- **Note: The graph was built from `app_orig_copy/`, but active development occurs in `app/`. Use `graphify update .` to re-index the current codebase.**
