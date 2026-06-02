# Creator RAG Analyzer: Production Architecture & Trade-offs

This repository contains the full-stack engineering prototype for a multimodal RAG pipeline built to ingest cross-platform creator data (YouTube transcripts and Instagram Reels metrics) and expose them through a low-latency, streaming AI chat interface.

The goal wasn't just to write an LLM wrapper, but to solve the actual infrastructure, memory, and scraping hurdles that occur when moving decoupled Python and Next.js applications into a cloud environment.

## Technical Stack & Topology

- **Frontend:** Next.js 15 (App Router, Turbopack) using the native `ReadableStream` API to process chunked tokens over raw JSON responses. Hosted on Vercel.
- **Backend:** FastAPI (Uvicorn ASGI) handling cross-origin streams and coordination. Hosted on Render.
- **Vector Store:** Qdrant Cloud (Managed Cluster) via the `qdrant-client` SDK.
- **Embeddings:** HuggingFace Inference API (`sentence-transformers/all-MiniLM-L6-v2`) via LangChain.
- **LLM Core:** Groq API running `llama-3.1-8b-instant` for sub-second streaming inference.

## Production Battle Scars: Hard Engineering Decisions

### 1. The 512MB RAM Crash (Local vs. Cloud Embeddings)

During local testing, I utilized a local instance of `langchain-huggingface` running PyTorch to generate vector embeddings. It worked flawlessly on my machine. However, when deploying to Render's free tier, the container instantly suffered `OOM (Out of Memory)` fatal crashes during startup because loading PyTorch and the model weights exceeded the strict 512MB RAM ceiling.

- **The Decision:** Instead of asking for a paid upgrade, I refactored the entire embedding pipeline. I removed PyTorch and heavy deep-learning dependencies entirely from `requirements.txt`, dropping the deployment image size from over 1.5GB to under 100MB. I swapped the architecture to offload embedding generation to the asynchronous **HuggingFace Inference API**. This kept the pipeline lightweight, completely free, and computationally efficient.

### 2. Bypassing the Data-Center IP Block

Once deployed on Render, the YouTube ingestion route immediately broke with `403 Sign in to confirm you’re not a bot` errors. This happened because `yt-dlp` requests were originating from data-center IP blocks flagged by YouTube’s automated scraping defense systems.

- **The Decision:** I modified the backend initialization sequence to look for an absolute path targeting a Netscape-formatted authentication cookie file (`youtube_cookies.txt`). Furthermore, when handling YouTube Shorts or unusual audio streams, `yt-dlp` would throw format availability exceptions. I patched the extraction configurations to enforce `ignore_no_formats_error: True` and fallback stream selection, allowing metadata harvesting to succeed smoothly.

### 3. State Management: The Cloud Vector Layer Pivot

Initially, the vector database targeted a local persistent storage directory (`./qdrant_data`). This works well locally but is completely unviable for ephemeral cloud instances (like Render or Heroku) which completely wipe the local disk state upon container sleep cycles or new code deployments.

- **The Decision:** I migrated the persistence layer to a **Qdrant Cloud Cluster**. I designed the connection manager around a lazy-loaded singleton structure (`get_qdrant_client()`). This keeps network connections pooled efficiently and prevents the application from making dead connections or dropping index records during backend scale-downs.

### 4. Chunk Strategy: 500 Characters / 100 Overlap

Video and audio transcripts lack structural punctuation, headers, and markdown boundaries. They are unformatted streams of continuous text.

- **Why 500 Characters:** This length represents roughly 20 to 30 seconds of spoken dialogue. Keeping chunks small ensures that highly specific data metrics or programmatic conversational contexts do not get diluted inside the multi-dimensional vector space.
- **Why 100 Overlap:** This acts as a buffer to preserve structural continuity. It guarantees that semantic concepts or critical analytics metrics that happen to be split directly at a 500-character boundary remain fully retrievable across adjacent windows.

## System Vulnerabilities: What Breaks at Scale?

If this platform scale shifts tomorrow to 1,000 creators or 10,000 concurrent users, the architecture will saturate in two critical locations:

### 1. Synchronous Network I/O Saturation

Right now, the `/ingest` route handles URL validation, metadata parsing, and vector ingestion synchronously within FastAPI's context. Under massive concurrent loads, the server event loop will saturate waiting for remote network callbacks from YouTube and Instagram, degrading API responsiveness and causing `504 Gateway Timeouts`.

- **The Fix:** Move to a decoupled, event-driven worker model. The ingestion route should immediately return a `202 Accepted` status with a unique job UUID, handing off the intensive asset collection to an asynchronous worker pool (Celery or RabbitMQ + Redis). The Next.js frontend can then either poll a status endpoint or listen to a WebSocket connection for ingestion updates.

### 2. Instagram's Rate Limit Wall

While YouTube is managed via persistent browser cookies, Instagram relies on raw requests that will immediately trigger rate-limiting if pounded by thousands of requests from a single server IP.

- **The Fix:** Integrate a dynamic, proxy-rotating middleware layer into the ingestion module. All external HTTP requests targeting creator platform endpoints must be routed through a pool of residential proxies with rotating signatures to prevent automated behavioral profiling.

## Local Development Flow

### 1. Backend Environment Setup

Ensure you have Python 3.11+ installed.

Bash

```
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / MacOS
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Create a `.env` file in the root of the `backend` folder:

Code snippet

```
GROQ_API_KEY="your_groq_api_key"
HF_TOKEN="your_huggingface_inference_api_token"
QDRANT_URL="your_qdrant_cloud_cluster_url"
QDRANT_API_KEY="your_qdrant_api_key"
FRONTEND_URL="http://localhost:3000"
```

### 2. Frontend Development Setup

Ensure you have Node.js 18+ installed.

Bash

```
cd frontend
npm install
npm run dev
```

Create a `.env.local` file in the root of the `frontend` folder:

Code snippet

```
NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
```
