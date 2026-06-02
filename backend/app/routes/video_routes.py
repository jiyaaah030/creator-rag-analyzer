from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.youtube_service import get_youtube_data
from app.services.instagram_service import get_instagram_data
from app.rag.vector_store import store_transcript
from app.services.chat_service import get_chat_chain

router = APIRouter()

class VideoUrls(BaseModel):
    youtube_url: str
    instagram_url: str

class ChatRequest(BaseModel):
    question: str
    metadata: dict = None  # Added to capture frontend card metrics

@router.post("/ingest")
def ingest_videos(urls: VideoUrls):
    print("Starting unified ingestion process...")
    
    yt_data = get_youtube_data(urls.youtube_url)
    if "error" in yt_data:
        raise HTTPException(status_code=400, detail=f"YouTube Error: {yt_data['error']}")
        
    ig_data = get_instagram_data(urls.instagram_url)
    if "error" in ig_data and not ig_data.get("metadata"):
         raise HTTPException(status_code=400, detail=f"Instagram Error: {ig_data['error']}")
         
    print("Chunking and storing YouTube data...")
    yt_store_result = store_transcript(yt_data["transcript"], yt_data["metadata"])
    
    print("Chunking and storing Instagram data...")
    ig_store_result = store_transcript(ig_data["transcript"], ig_data["metadata"])
    
    return {
        "status": "success",
        "message": "Both videos processed and embedded successfully.",
        "data": {
            "youtube": {
                "metadata": yt_data["metadata"],
                "chunks": yt_store_result["chunks_stored"]
            },
            "instagram": {
                "metadata": ig_data["metadata"],
                "chunks": ig_store_result["chunks_stored"]
            }
        }
    }

@router.post("/chat")
def chat_stream(request: ChatRequest):
    print(f"Received question: {request.question}")
    try:
        # Pass the metadata down to the chat chain handler
        chain = get_chat_chain(request.metadata)
        
        def event_stream():
            for chunk in chain.stream(request.question):
                yield chunk

        return StreamingResponse(event_stream(), media_type="text/plain")

    except Exception as e:
        print("CHAT ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))