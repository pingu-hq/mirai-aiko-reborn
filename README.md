# Mirai Aiko (Reborn)

**A personal AI‑powered chatbot that remembers you.**
Built with FastAPI, Redis‑based opaque‑token authentication, MongoDB, and a vector store (Milvus) + mem0 for long‑term, contextual memory. Heavy LLM work is off‑loaded to a NATS‑driven worker, while the front‑end receives real‑time replies via Server‑Sent Events (SSE).

---

## Vision

We aim to provide a **self‑hosted, privacy‑first personal assistant** that can:

* Understand a user’s history and preferences through persistent memory.
* Answer questions, set reminders, and perform simple actions while staying within the user’s context.
* Be extended with new tools (web‑search, code execution, calendar integration, etc.) without breaking the core workflow.

---

## Core Features

- **Opaque‑token cookie auth** (Redis) – secure, stateless, and works seamlessly with SSE.
- **Async‑first architecture** – FastAPI + NATS job queue ensures the API never blocks, even when CrewAI/LLM calls are heavy.
- **Contextual memory** – `mem0` + Milvus vector store provides both short‑term cache and long‑term RAG‑style recall.
- **Deterministic CrewAI pipeline** – “Lily → Lotus” multi‑agent flow gives predictable, step‑by‑step reasoning.
- **Extensible tooling** – new agents, tools, or external services can be added by dropping a YAML/TOML definition and wiring a small service.
- **Web UI (HTMX + Tailwind CSS + Alpine.js)** – a minimal, reactive chat interface that can be run locally for testing or further customization.

---

## Architecture Overview

```
POST /api/chat
   │
   └─► Validate opaque cookie (Redis)
        │
        └─► Publish job (payload + job_id) to NATS
             │
             └─► Return job_id to client
```

- **Worker process** (separate Docker service) subscribes to the NATS job subject, runs the Lily/Lotus agents, writes progress/results back to a NATS event subject `chat.events.<job_id>`.
- **SSE endpoint** (`GET /api/chat/stream?job_id=…`) re‑validates the same cookie, subscribes to that event subject, and streams token‑by‑token updates to the browser.
- **Memory stack** – short‑term TTL cache + per‑user lock (Redis) + long‑term Milvus vector store (mem0) gives the assistant a persistent “understanding” of each user.

---

## Extending the Assistant

1. **Add a new tool definition** (`tools.yaml` or new TOML file) describing the external capability (e.g., web‑search, calendar API).
2. **Implement a service** in `app/services/agents/` that calls the external API.
3. **Update the CrewAI task/agent YAML** to reference the new tool.
4. **Restart the NATS worker** – the new capability is instantly available without changing the API layer.

---

## Minimal Web UI

A lightweight HTML page located at `frontend/` (served via FastAPI static files) uses:

- **HTMX** – to fire the `POST /api/chat` request and open the SSE stream without custom JavaScript.
- **Tailwind CSS** – for a clean, responsive layout.
- **Alpine.js** – for local state handling (message list, loading spinner, error handling).

The UI is deliberately simple so you can:

- Test the end‑to‑end flow locally.
- Extend the markup or add new UI components (e.g., reminder list, settings) as needed.

---

## Getting Started

```bash
# Install dependencies (uv is used)
uv sync

# Run the API (development)
uv run python main.py

# In another terminal, start the NATS worker
uv run python -m app.worker   # (you’ll add this entrypoint)

# Open the UI
http://localhost:8000/
```

*Make sure Redis, MongoDB, Milvus, and NATS are reachable (Docker‑compose can spin them all up).*

---

## License

MIT – feel free to fork, tweak, and run your own personal assistant.
