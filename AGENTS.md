- Run dev server from repo root: `uv sync` then `uv run python main.py`.
- FastAPI app startup (Redis+Mongo): `main.py` lifespan calls `RedisCacheBaseRepository.init_redis_cache_repository()` and `MongoBase.init_mongo_client()`; required env vars are `REDIS_URI` and `MONGO_URI`.
- Env loading: `app/core/config.py` runs `load_dotenv()` at import time, so `.env` is loaded from the current working directory; keep a complete root `.env` (not only `secrets/.env`) including `MILVUS_COLLECTION_NAME` if you use memory.
- Docker/local dependencies: `docker-compose.yaml` starts Mongo+Redis and maps the backend to `127.0.0.1:8000` (Mongo/Redis ports are not exposed).
- Default routing: `main.py` mounts only `app/routers/auth_router.py` under `/api/auth` and exposes `/health-check`—playground/chat routes in `app_orig_copy/routers/*` will 404 unless you wire them in.
- Auth endpoints to hit: `GET /api/auth/sample-user-for-testing`, `POST /api/auth/register-user`, `POST /api/auth/login-user`, `GET /api/auth/me`, `GET /api/auth/logout`.
- Cookie auth details: cookies are named `access` and `refresh` (opaque Redis tokens); `IS_DEPLOYED_FOR_PRODUCTION=true` makes them `secure`, and cookie `samesite` is `lax` (access) / `strict` (refresh).
- Token TTL + rotation gotcha: Redis token TTLs match cookie TTLs (`access` = 7 minutes, `refresh` = 7 days); `GET /api/auth/me` calls `HttpCookieAuthService.get_user_id()` which deletes the old refresh token and re-issues both cookies when access is missing.
- LLM/memory initialization: `AgentMemoryRepository` needs `COHERE_API_KEY`, `GROQ_API_KEY`, `MILVUS_URI`, `MILVUS_TOKEN`, `MILVUS_COLLECTION_NAME`; call `AgentMemoryRepository.init_memory_client()` before use and `close_memory_client()` during shutdown.
- Workflow example locations: `app/workflows/agent_pipeline.py` is currently a stub; for end-to-end agent/LLM examples, prefer `app_orig_copy/routers/*` and `app_orig_copy/services/*`.
- Graphify workflow: with `graphify-out/graph.json` present, start codebase questions with `graphify query "..."` (and `graphify path "A" "B"` for relationships), and after edits run `graphify update .`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
