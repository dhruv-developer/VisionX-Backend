from fastapi import APIRouter, Query
from config import groq_client
from database import db
from services.course_service import fetch_courses
from services.agent_service import run_agents
from utils.email_service import send_course_recommendation_email
from bson import ObjectId
import logging

router = APIRouter()
users_collection = db["users"]

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)

@router.post("/recommend_courses/")
def recommend_courses(
    user_id: str, 
    send_email: bool = False,  # ✅ Default is False
    limit: int = Query(5, ge=1, le=10)  # ✅ Default limit is 5
):
    """Recommend courses based on quiz score, user needs, and scrape Udemy, YouTube, and Coursera."""
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"error": "User not found"}

    specialization = user["specialization"]
    quiz_score = user.get("quiz_score", 5)  # ✅ Default to 5 if missing
    budget = user.get("budget", 50)  # ✅ Default budget if not set
    required_level = user.get("preferred_difficulty", "Beginner")  # ✅ Default to Beginner

    logging.info(f"📌 Fetching AI + Real Course Recommendations for {specialization} (Level: {required_level}, Budget: ${budget})")

    # ✅ Run AI Agents to Filter Courses
    try:
        agent_recommendations = run_agents(specialization, quiz_score, required_level)
        logging.info(f"🤖 AI Agent Recommendations: {len(agent_recommendations)} courses found.")
    except Exception as e:
        logging.error(f"❌ AI Agent Error: {e}")
        agent_recommendations = []

    # ✅ Fetch Courses by Scraping Udemy, YouTube (via API), Coursera
    scraped_courses = fetch_courses(specialization, budget, required_level)

    # ✅ Ensure YouTube courses are fetched properly
    if "youtube" not in scraped_courses or not scraped_courses["youtube"]:
        logging.warning("⚠️ No YouTube courses found. Check API key or quota limits.")

    # ✅ Handle missing AI recommendations
    if not agent_recommendations:
        logging.warning("⚠️ AI Agent did not return any recommendations.")

    # ✅ Limit final recommendations properly
    final_courses = (agent_recommendations[:limit] + 
                     scraped_courses["udemy"][:limit] + 
                     scraped_courses["coursera"][:limit] + 
                     scraped_courses["youtube"][:limit])

    # ✅ Ensure every course has a valid link
    for course in final_courses:
        if "link" not in course or not course["link"]:
            course["link"] = "#"

    # ✅ Send Email if Requested
    if send_email:
        logging.info(f"📩 Sending course recommendations to {user['email']}...")
        success = send_course_recommendation_email(user["email"], final_courses)
        if success:
            logging.info("✅ Email sent successfully!")
        else:
            logging.error("❌ Email sending failed!")

    return {
        "final_recommendations": final_courses,
        "scraped_courses": scraped_courses
    }
