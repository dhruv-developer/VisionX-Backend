import requests
import yt_dlp
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

def fetch_udemy_courses(topic, budget, level):
    """Fetch Udemy courses dynamically."""
    url = f"https://www.udemy.com/courses/search/?q={topic}+{level}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    courses = []
    for course in soup.find_all("div", class_="course-card--course-title"):
        courses.append({
            "title": course.text,
            "price": 10,  # ✅ Assume $10 for now
            "platform": "Udemy",
            "link": "https://www.udemy.com"  # ✅ Placeholder, should extract real link
        })

    return [c for c in courses if c["price"] <= budget]

def fetch_coursera_courses(topic):
    """Fetch Coursera courses dynamically."""
    url = f"https://api.coursera.org/api/courses.v1?q=search&query={topic}"
    response = requests.get(url)
    courses = response.json().get("elements", [])
    return [{"title": c.get("name", "Unknown Course"), "platform": "Coursera", "link": f"https://www.coursera.org/learn/{c.get('slug', '')}"} for c in courses]

def fetch_youtube_videos(topic):
    """Fetch YouTube courses dynamically."""
    ydl_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_result = ydl.extract_info(f"ytsearch10:{topic}", download=False)
        return [{"title": v["title"], "platform": "YouTube", "link": v["webpage_url"]} for v in search_result.get("entries", [])]

def fetch_courses(topic, budget, level):
    """Fetch courses from Udemy, Coursera, and YouTube."""
    return {
        "udemy": fetch_udemy_courses(topic, budget, level),
        "coursera": fetch_coursera_courses(topic),
        "youtube": fetch_youtube_videos(topic)
    }
