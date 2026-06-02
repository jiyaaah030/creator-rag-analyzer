# Creator RAG Analyzer (Internal Architecture & Trade-offs)

A localized multimodal RAG pipeline built over a weekend to ingest, parse, and semantically query cross-platform creator content (YouTube transcripts + Instagram Reels metadata).

The goal was simple: get a low-latency, streaming engineering prototype up and running without burning API credits on third-party model providers for structural tasks like text embeddings.

## The Architecture Stack

- **Frontend:** Next.js 15 (App Router, Turbopack) using native `ReadableStream` for chunked rendering.
- **Backend:** FastAPI (Uvicorn ASGI) handling stream generation.
- **Embeddings Engine:** Local HuggingFace `all-MiniLM-L6-v2` via `langchain-huggingface`.
- **Vector Layer:** Qdrant (Disk-persisted local storage).
- **Inference Layer:** Groq Engine (`llama-3.1-8b-instant`).

## Architectural Decisions & Trade-offs

### 1. Why Qdrant over ChromaDB or FAISS?

I chose Qdrant because of its native support for payload filtering and its underlying Rust implementation. In a cross-platform creator analysis tool, queries are rarely purely semantic. Users ask questions restricted to specific platforms (e.g., "Compare _only_ my Instagram engagement metrics"). Qdrant allows us to apply metadata filters directly to the vector payload before running the HNSW vector search, avoiding semantic dilution.

**The Local File-Lock Scar:** During development on Windows with Uvicorn’s `--reload` process monitor, global module instantiation of the Qdrant client caused multi-process file deadlocks (`portalocker.exceptions.AlreadyLocked`). I refactored the vector layer to use a lazy-loaded singleton pattern (`get_qdrant_client()`), ensuring the database disk lock is only claimed inside execution threads rather than on module import.

### 2. Why Chunk Size 500 with 100 Overlap?

Video transcripts are not structured prose—they lack natural paragraph breaks, punctuation, and markdown semantics. They are continuous streams of spoken dialogue.

- **500 Character Chunk Size:** This equates to roughly 20 to 30 seconds of real-time speech. Keeping chunks this tight ensures that specific metrics or conversational hooks aren't watered down by minutes of unrelated talking points inside the embedding space.
- **100 Character Overlap:** Essential for preventing structural truncation. Since scripts are parsed raw, a 100-character safety boundary guarantees that contextual phrases or numbers split across windows remain semantically retrievable.

### 3. Context Injection vs Fine-Tuning

To get the LLM to understand high-level card metrics (views, likes, comments) which _do not_ exist in spoken video transcripts, I updated the chat pipeline to dynamically build a `metrics_summary` context block on the fly. This block is hard-injected straight into the system prompt alongside the semantic text blocks retrieved from Qdrant. This hybrid context model forces the LLM to ground its qualitative analysis in raw, quantitative performance numbers without needing to maintain expensive real-time fine-tuning steps.

## What Breaks at Scale? (1,000 Creators / 10,000 Users)

If this repo hits real production load tomorrow, it will break in three distinct places. Here is the post-mortem before it happens:

### 1. The Instagram Ingestion Wall

Right now, `yt-dlp` handles the asset parsing inside a synchronous block within our FastAPI endpoints. This works fine for single execution tests on a local machine. However, at 1,000 creators a day, Instagram will flag the deployment server’s IP and trigger aggressive rate-limiting or anti-bot blocks within minutes, resulting in empty metrics payloads.

- _The Fix:_ Decouple the ingestion pipeline completely. Move ingestion tasks to an asynchronous task queue (Celery + Redis) and route all structural extraction requests through rotating residential proxy networks.

### 2. Synchronous Network I/O Deadlocks

Currently, when a user drops a URL, the server waits synchronously for the video metadata and transcript to download before completing the request. Under concurrent load from 10,000 users, FastAPI's event loop will saturate waiting for third-party network responses, causing massive API degradation and `504 Gateway Timeouts`.

- _The Fix:_ Implement a non-blocking webhook architecture. The user submits a URL, the backend immediately returns a `202 Accepted` with a job ID, and the frontend polls or listens via WebSockets while Celery handles the extraction in the background.

### 3. Ephemeral Storage Corruption

The current database relies on a local disk path (`./qdrant_data`). If deployed on a standard ephemeral server instance (like Render or Heroku standard dynos), the database state is completely destroyed every time the container restarts or re-deploys.

- _The Fix:_ Migrate the local configuration to a dedicated cloud cluster instance or hook up a persistent network block storage volume (AWS EBS / persistent disk mounts) to retain vector histories.

## Local Setup

### Backend (Python 3.11+)

Bash

```
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

_Requires a `.env` file containing `GROQ_API_KEY` in the backend root._

### Frontend (Next.js)

Bash

```
cd frontend
npm install
npm run dev
```

### Why this works perfectly:

1. It uses industry terminology correctly (**HNSW vector search, payload filtering, structural truncation, multi-process file deadlocks**).
2. It admits exactly what is wrong with the current setup and how to fix it, which shows you understand senior-level production architecture.
3. It directly calls out the exact Windows error you ran into and fixed, proving you actually wrote and debugged the codebase yourself.
