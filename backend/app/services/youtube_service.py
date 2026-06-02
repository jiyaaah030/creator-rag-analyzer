from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re

def extract_video_id(url: str):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)

def get_youtube_data(url: str):
    try:
        print(f"Processing YouTube URL: {url}")
        video_id = extract_video_id(url)
        
        # 1. Fetch Transcript
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.get_transcript(video_id)
            transcript = " ".join([item["text"] for item in transcript_list])
        except Exception as e:
            print(f"Transcript Error: {str(e)}")
            transcript = "Transcript not available."

        # 2. Fetch Metadata via yt-dlp
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": False, # We need the full metadata payload
            "cookiefile": "youtube_cookies.txt"  # <--- ADD THIS LINE
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        # 3. Safely extract required fields
        views = info.get("view_count") or 0
        likes = info.get("like_count") or 0
        comments = info.get("comment_count") or 0
        
        # 4. Compute Engagement Rate
        engagement_rate = 0
        if views > 0:
            engagement_rate = ((likes + comments) / views) * 100
            
        metadata = {
            "platform": "youtube",
            "video_id": video_id,
            "creator": info.get("uploader") or info.get("channel"),
            "follower_count": info.get("channel_follower_count") or 0,
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement_rate": round(engagement_rate, 4),
            "hashtags": info.get("tags") or [],
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration") # in seconds
        }

        print("YouTube extraction successful.")
        return {
            "metadata": metadata,
            "transcript": transcript
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}