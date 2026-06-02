Creator Intelligence System (RAG)
A full-stack RAG pipeline designed to extract, embed, and compare social media content performance (YouTube & Instagram) in real-time.

Instead of a standard OpenAI-wrapper chatbot, this system implements a heavily optimized, zero-cost architecture using local HuggingFace embeddings, in-memory vector storage, and Groq's LPU infrastructure for sub-second streaming responses.

Architecture & Tech Stack
Frontend: Next.js, React, Tailwind CSS (Native ReadableStream for token streaming)

Backend: FastAPI, Python (Async orchestration)

Data Extraction: yt-dlp, youtube-transcript-api

RAG Pipeline: LangChain (LCEL)

Vector Database: Qdrant (Local disk persistence)

Embeddings: HuggingFace all-MiniLM-L6-v2 (Local, $0 cost)

LLM: Groq llama-3.1-8b-instant (High-speed generation, $0 cost)

Core Features
Unified Ingestion: Simultaneously parses YouTube and Instagram URLs, extracting transcripts and metadata (views, likes, comments, creator details).

Dynamic Fallbacks: Gracefully handles platform rate-limiting (e.g., hidden IG view counts) without breaking the UI or backend logic.

Contextual Intelligence: Injects quantitative metrics (Engagement Rate) alongside qualitative semantic chunks into the LLM prompt.

Streaming UI: Token-by-token streaming response to minimize perceived latency.

Local Setup
You will need two terminal windows running concurrently to run the full stack.

1. Backend Environment
   Bash
   cd backend
   python -m venv venv
   source venv/bin/activate # On Windows use: venv\Scripts\activate

# Install dependencies

pip install fastapi uvicorn pydantic langchain langchain-openai langchain-groq langchain-huggingface langchain-qdrant qdrant-client youtube-transcript-api yt-dlp sentence-transformers
Create a .env file in the backend directory:

Code snippet
GROQ_API_KEY=your_groq_api_key_here
Start the API:

Bash
uvicorn app.main:app --reload 2. Frontend Environment
Bash
cd frontend
npm install
npm run dev
Access the dashboard at http://localhost:3000.

Production & Scalability Roadmap
How to scale this pipeline to handle 1,000+ creators daily:

Decoupled Ingestion: Move the yt-dlp extraction phase out of the synchronous FastAPI route and into an async Celery worker pool backed by Redis to prevent API timeouts during heavy transcript downloads.

Proxy Rotation: Instagram aggressively rate-limits unauthenticated scraping. Production extraction must be routed through rotating residential proxies or migrated to the official Graph API.

Vector Distribution: Migrate Qdrant from local disk storage to a managed cloud cluster to allow horizontal scaling of the semantic search queries.
