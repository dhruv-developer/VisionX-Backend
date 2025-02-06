from fastapi import APIRouter, Query
from config import groq_client
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from utils.email_service import send_email
import re
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)

# Supported Languages
LANGUAGES = {
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu", 
    "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi", "pa": "Punjabi", 
    "gu": "Gujarati", "ur": "Urdu"
}

def get_video_id(youtube_url: str):
    """Extracts video ID from a YouTube URL."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
    return match.group(1) if match else None

def fetch_transcript(video_id: str):
    """Fetches transcript from a YouTube video."""
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript_data])
    except Exception as e:
        logging.error(f"❌ Transcript Error: {e}")
        return None

def summarize_transcript(transcript_text: str):
    """Summarizes the transcript using Groq Llama 3.3-70B."""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Summarize the following transcript in detail:\n\n{transcript_text}"}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"❌ Summarization Error: {e}")
        return None

def translate_summary(summary: str, language_code: str):
    """Translates the summary into a selected regional language."""
    try:
        return GoogleTranslator(source="auto", target=language_code).translate(summary)
    except Exception as e:
        logging.error(f"❌ Translation Error: {e}")
        return None

def send_summary_email(to_email, video_url, summary, language):
    """Send an email with the YouTube summary."""
    subject = "📺 Intellica - Your YouTube Video Summary"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="color: #007bff; text-align: center;">Your YouTube Video Summary 🎥</h2>
        <p style="text-align: center;"><b>Video URL:</b> <a href="{video_url}" style="color: #007bff;">Watch Video</a></p>
        <p><b>Summary ({language}):</b></p>
        <p style="border-left: 4px solid #007bff; padding-left: 10px;">{summary}</p>
        <hr style="border: 0; height: 1px; background: #ddd;">
        <p style="text-align: center;">Happy Learning! 🚀</p>
        <p style="text-align: center;"><b>Best Regards,<br>Intellica Team</b></p>
    </div>
    """

    return send_email(to_email, subject, html_content)

@router.post("/youtube_summary/")
def youtube_summary(
    youtube_url: str, 
    language_code: str = "en", 
    send_email: bool = False, 
    user_email: str = Query(None, title="User Email (Required if send_email=true)")
):
    """Extracts, summarizes, translates YouTube video transcripts & optionally emails the summary."""
    video_id = get_video_id(youtube_url)
    if not video_id:
        return {"error": "Invalid YouTube URL. Please enter a valid link."}

    logging.info(f"📹 Fetching transcript for {youtube_url}...")
    transcript = fetch_transcript(video_id)
    if not transcript:
        return {"error": "Transcript not available for this video."}

    logging.info("📝 Generating summary...")
    summary = summarize_transcript(transcript)
    if not summary:
        return {"error": "Failed to generate summary."}

    if language_code != "en" and language_code in LANGUAGES:
        logging.info(f"🌍 Translating summary to {LANGUAGES[language_code]}...")
        translated_summary = translate_summary(summary, language_code)
        if not translated_summary:
            return {"error": f"Failed to translate to {LANGUAGES[language_code]}"}
    else:
        translated_summary = summary

    response_data = {
        "video_url": youtube_url,
        "summary": translated_summary,
        "language": LANGUAGES.get(language_code, "English")
    }

    if send_email and user_email:
        logging.info(f"📩 Sending summary to {user_email}...")
        email_sent = send_summary_email(user_email, youtube_url, translated_summary, LANGUAGES.get(language_code, "English"))
        response_data["email_status"] = "Summary emailed successfully!" if email_sent else "Failed to send email."

    return response_data
