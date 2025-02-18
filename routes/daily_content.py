from fastapi import APIRouter, HTTPException, Query, Depends
import requests
from bs4 import BeautifulSoup
import json
import logging
from config import groq_client
from utils.email_service import send_email
from database import db
from bson import ObjectId
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from models import UserProfile

router = APIRouter()
users_collection = db["users"]

# ✅ Load MiniLM model once for embeddings
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

logging.basicConfig(level=logging.INFO)

def get_user_from_db(user_id: str):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logging.error(f"Invalid User ID Format: {e}")
        raise HTTPException(status_code=400, detail="Invalid User ID format")

# ✅ Fetch multiple news sources dynamically
def fetch_news_articles(query):
    sources = {
        "Medium": f"https://medium.com/search?q={query}",
        "Google News": f"https://news.google.com/search?q={query}",
        "TechCrunch": f"https://techcrunch.com/search/{query}/",
    }
    
    articles = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for source, url in sources.items():
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            continue
        
        soup = BeautifulSoup(response.text, "html.parser")
        found_articles = soup.find_all("h3")[:3]  # Fetch top 3 articles
        
        for article in found_articles:
            link_tag = article.find("a", href=True)
            if link_tag:
                articles.append({
                    "source": source,
                    "title": article.text.strip(),
                    "url": link_tag["href"].split("?")[0]
                })
    return articles[:5] if articles else None  # Limit to 5 articles

# ✅ AI-generated article summary
def generate_ai_summary(article_title, article_url):
    summary_prompt = f"""
    Summarize this article in 3 sentences:
    Title: {article_title}
    Link: {article_url}
    """
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": summary_prompt}],
        model="llama-3.3-70b-versatile",
    )
    try:
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        return {"summary": "Could not generate summary.", "key_takeaway": "Read the full article for details."}

# ✅ AI-generated Problem of the Day
def generate_ai_problem(user):
    problem_prompt = f"""
    Create a challenging problem in {user['specialization']}.
    Difficulty: {user.get('preferred_difficulty', 'Beginner')}.
    Quiz Score: {user.get('quiz_score', 'N/A')}.
    """
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": problem_prompt}],
        model="llama-3.3-70b-versatile",
    )
    try:
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        return {"problem": "An interesting problem to test your skills.", "hint": "Think logically!"}

# ✅ Route: AI-Powered Daily Content (Multi-Agent)
@router.post("/daily-content/")
def get_daily_content(user_id: str, send_email: bool = False, user_email: str = Query(None)):
    user = get_user_from_db(user_id)
    articles = fetch_news_articles(user["specialization"])
    if not articles:
        raise HTTPException(status_code=404, detail="No articles found.")
    
    summarized_articles = [
        {**article, **generate_ai_summary(article["title"], article["url"])} for article in articles
    ]
    
    problem_of_the_day = generate_ai_problem(user)
    
    daily_content = {
        "user": user["name"],
        "problem_of_the_day": problem_of_the_day,
        "news_articles": summarized_articles
    }
    
    if send_email and user_email:
        email_status = send_daily_content_email(user_email, daily_content)
    else:
        email_status = "Email not sent."
    
    return {**daily_content, "email_status": email_status}

# ✅ Function: Send Daily Content Email
def send_daily_content_email(to_email, content):
    subject = "📢 Your AI-Powered Daily Insights"
    email_content = f"""
    <h2>🚀 Daily Insights & Challenges</h2>
    <h3>🧠 Problem of the Day</h3>
    <p><b>Problem:</b> {content['problem_of_the_day']['problem']}</p>
    <p><b>Hint:</b> {content['problem_of_the_day']['hint']}</p>
    
    <h3>📰 Today's News</h3>
    """
    
    for article in content['news_articles']:
        email_content += f"<p><b>{article['title']}</b> ({article['source']})</p><p>{article['summary']}</p><a href='{article['url']}'>Read More</a><hr>"
    
    return "Email sent successfully!" if send_email(to_email, subject, email_content) else "Failed to send email."
