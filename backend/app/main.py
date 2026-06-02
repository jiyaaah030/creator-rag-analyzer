from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.video_routes import router as video_router
import os

app = FastAPI()

# Dynamically read the production frontend URL from environment variables.
# Fall back to localhost for local testing.
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

origins = [
    frontend_url,
    "https://creator-rag-analyzer.vercel.app", 
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, PUT, DELETE, etc.
    allow_headers=["*"],  # Allows all headers (Content-Type, Authorization, etc.)
)

app.include_router(video_router)

@app.get("/")
def root():
    return {"message": "Creator Intelligence API Running"}