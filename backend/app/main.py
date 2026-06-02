from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.video_routes import router as video_router
import os

app = FastAPI()

# Dynamically read the production frontend URL from environment variables.
# Fall back to localhost for local testing.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)

@app.get("/")
def root():
    return {"message": "Creator Intelligence API Running"}