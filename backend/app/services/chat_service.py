from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.rag.vector_store import get_retriever
import os
from dotenv import load_dotenv

load_dotenv()

def get_chat_chain(frontend_metadata=None):
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        streaming=True
    )

    retriever = get_retriever()

    # Format the high-level performance metrics into a readable string block
    metrics_summary = "No high-level metrics available."
    if frontend_metadata:
        yt = frontend_metadata.get("youtube", {}).get("metadata", {})
        ig = frontend_metadata.get("instagram", {}).get("metadata", {})
        
        metrics_summary = f"""
        YOUTUBE METRICS:
        - Creator/Channel: {yt.get('creator', 'Unknown')}
        - Views: {yt.get('views', 0)}
        - Likes: {yt.get('likes', 0)}
        - Comments: {yt.get('comments', 0)}
        - Engagement Rate: {yt.get('engagement_rate', 0)}%

        INSTAGRAM METRICS:
        - Creator/Account: {ig.get('creator', 'Unknown')}
        - Views/Plays: {ig.get('views', 0)}
        - Likes: {ig.get('likes', 0)}
        - Comments: {ig.get('comments', 0)}
        - Engagement Rate: {ig.get('engagement_rate', 0)}%
        """

    # Upgraded template that explicitly provides both metrics AND transcript context
    template = f"""You are a highly analytical creator intelligence AI.
    Your job is to compare social media content performance based on high-level video metrics and transcript details.
    
    HIGH-LEVEL VIDEO PERFORMANCE METRICS:
    {metrics_summary}

    RULES:
    1. Utilize BOTH the high-level metrics above and the transcript chunks below to formulate deep comparative answers.
    2. Always clearly cite whether your data comes from the Metrics Summary or the Transcript Chunks.
    3. If asked about performance, view counts, or engagement rates, use the high-level metrics provided above.

    TRANSCRIPT CHUNKS CONTEXT:
    {{context}}

    User Question: {{question}}
    
    Answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        formatted = []
        for doc in docs:
            meta = doc.metadata
            source_info = f"[Video ID: {meta.get('video_id', 'Unknown')} | Platform: {meta.get('platform', 'Unknown')}]"
            formatted.append(f"{source_info}\nContent: {doc.page_content}")
        return "\n\n---\n\n".join(formatted)

    # Build the chain
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain