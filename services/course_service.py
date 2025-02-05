import requests
from bs4 import BeautifulSoup
import yt_dlp

def fetch_udemy_courses(topic, budget):
    try:
        url = f"https://www.udemy.com/courses/search/?q={topic}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        courses = []
        for course in soup.find_all("div", class_="course-card--course-title"):
            course_title = course.text
            price = "Varies"
            if "price" in course.attrs:  
                price = float(course.attrs["price"])
                if price > budget:
                    continue  # Ignore courses above budget

            courses.append({"title": course_title, "price": price, "platform": "Udemy"})

        return courses[:10]
    except Exception as e:
        return {"error": str(e)}

def fetch_coursera_courses(topic):
    try:
        url = f"https://api.coursera.org/api/courses.v1?q=search&query={topic}"
        response = requests.get(url)
        courses = response.json().get("elements", [])
        return [{"title": c.get("name", "Unknown Course"), "platform": "Coursera"} for c in courses]
    except Exception as e:
        return {"error": str(e)}

def fetch_youtube_videos(topic):
    try:
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch10:{topic}", download=False)
            videos = search_result.get("entries", [])

        return [{"title": v["title"], "url": v["webpage_url"], "platform": "YouTube"} for v in videos[:10]]
    except Exception as e:
        return {"error": str(e)}

def fetch_courses(topic, preferred_platform, budget):
    """
    Fetches courses from multiple platforms based on the user's preferred platform and budget.
    """
    courses = {
        "udemy": fetch_udemy_courses(topic, budget),
        "coursera": fetch_coursera_courses(topic),
        "youtube": fetch_youtube_videos(topic)
    }

    return {preferred_platform: courses.get(preferred_platform, [])}
