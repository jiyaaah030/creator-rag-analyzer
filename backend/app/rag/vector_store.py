# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Global tracking variable for the singleton client instance
_client_instance = None
COLLECTION_NAME = "youtube_rag"

# print("Loading HuggingFace embeddings...")
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("Connecting to HuggingFace Inference API...")
hf_token = os.getenv("HF_TOKEN")
embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=hf_token,
)

def get_qdrant_client():
    """Lazily initializes the Qdrant client, preferring cloud credentials if available."""
    global _client_instance
    if _client_instance is None:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if qdrant_url and qdrant_api_key:
            print("Connecting to Qdrant Cloud...")
            _client_instance = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            print("Connecting to Local Qdrant...")
            _client_instance = QdrantClient(path="./qdrant_data")
            
    return _client_instance


def create_collection():
    # Use the lazy client here to avoid global lock states
    client = get_qdrant_client()
    collections = client.get_collections().collections
    exists = any(col.name == COLLECTION_NAME for col in collections)

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,  # Matching MiniLM dimensions
                distance=Distance.COSINE
            ),
        )


def store_transcript(transcript_text: str, metadata: dict):
    client = get_qdrant_client()
    print("Creating collection if it doesn't exist...")
    create_collection()

    print("Splitting transcript...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    # Fixed typo: changed 'transcript' to 'transcript_text'
    chunks = splitter.split_text(transcript_text)
    print("Chunks created:", len(chunks))

    docs = []
    for chunk in chunks:
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "video_id": metadata.get("video_id", "unknown"),
                    "creator": metadata.get("creator", "unknown"),
                    "platform": metadata.get("platform", "unknown"),
                    "engagement_rate": metadata.get("engagement_rate", 0)
                }
            )
        )

    print("Initializing vector store for insertion...")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    print("Adding documents to vector DB...")
    vector_store.add_documents(docs)
    print("Documents stored successfully.")

    return {
        "chunks_stored": len(chunks)
    }


def get_retriever():
    # Fixed: Use the lazy client helper instead of the broken global client variable
    client = get_qdrant_client()
    print("Initializing vector store for retrieval...")
    
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    # Returns a retriever object configured to pull the top 5 match segments
    return vector_store.as_retriever(search_kwargs={"k": 5})