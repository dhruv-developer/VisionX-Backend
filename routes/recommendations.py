from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
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

# Exchange rate (Assumption: 1 USD ≈ 83 INR)
USD_TO_INR = 83  

class CourseRequest(BaseModel):
    user_id: str
    send_email: bool = False
    limit: int = Query(5, ge=1, le=10)  # ✅ Limit courses between 1 and 10

# ✅ Define Response Model
class Course(BaseModel):
    title: str
    platform: str
    rating: float
    price: float
    currency: str = "INR"
    link: str

class RecommendationResponse(BaseModel):
    final_recommendations: list[Course]
    scraped_courses: dict


@router.post("/recommend_courses/", response_model=RecommendationResponse)
def recommend_courses(request: CourseRequest):
    """Recommend courses based on quiz score, user needs, and scrape Udemy and Coursera (YouTube Removed)."""
    
    user = users_collection.find_one({"_id": ObjectId(request.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    specialization = user["specialization"]
    language = user.get("language", "English")  
    quiz_score = user.get("quiz_score", 5)  
    budget_usd = user.get("budget", 50)  
    budget_inr = budget_usd * USD_TO_INR  
    required_level = user.get("preferred_difficulty", "Beginner")  
    embeddings = user["generated_embedding"]

    logging.info(f"📌 Fetching AI + Real Course Recommendations for {specialization} (Level: {required_level}, Budget: ₹{budget_inr})")

    # ✅ Run AI Agents to Filter Courses
    agent_recommendations = run_agents(specialization, quiz_score, required_level, language, embeddings)

    # ✅ Fetch Courses by Scraping Udemy and Coursera (YouTube Removed)
    scraped_courses = fetch_courses(specialization, budget_inr, required_level, language)

    # ✅ Merge courses while maintaining limit
    final_courses = (
        agent_recommendations[:request.limit] +
        scraped_courses["udemy"][:request.limit] +
        scraped_courses["coursera"][:request.limit]
        # scraped_courses["youtube"][:request.limit]  # ❌ Removed YouTube
    )

    # ✅ Ensure valid course data
    validated_courses = []
    for course in final_courses:
        validated_courses.append(Course(
            title=course.get("title", "Unknown Course"),
            platform=course.get("platform", "Unknown"),
            rating=float(course.get("rating", 0.0)),
            price=float(course.get("price", 0.0)),
            link=course.get("link", "#")
        ))

    # ✅ Send Email if Requested
    if request.send_email:
        logging.info(f"📩 Sending course recommendations to {user['email']}...")
        success = send_course_recommendation_email(user["email"], validated_courses)
        if success:
            logging.info("✅ Email sent successfully!")
        else:
            logging.error("❌ Email sending failed!")

    return {
        "final_recommendations": validated_courses,
        "scraped_courses": scraped_courses
    }
