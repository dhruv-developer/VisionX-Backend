from fastapi import APIRouter
from config import groq_client
from database import users_collection
from services.course_service import fetch_courses
from services.embedding_service import match_courses
from bson import ObjectId
import json
import logging
import traceback
import re

router = APIRouter()

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)

def clean_json_response(response_text):
    """
    Cleans AI-generated text to ensure it is valid JSON before parsing.
    """
    response_text = response_text.strip()

    # Remove backticks if present
    if response_text.startswith("```") and response_text.endswith("```"):
        response_text = response_text[3:-3].strip()

    # Extract JSON using regex
    match = re.search(r'\{.*\}|\[.*\]', response_text, re.DOTALL)
    return match.group(0) if match else response_text

@router.post("/recommend_courses/")
def recommend_courses(user_id: str):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"error": "User not found"}

        if "quiz_score" not in user or "budget" not in user:
            return {"error": "Quiz score or budget missing. Please complete the quiz and set a budget first."}

        specialization = user['specialization']
        
        try:
            budget = float(user['budget'])  # Ensure budget is a float
        except ValueError:
            logging.error(f"Invalid budget format: {user['budget']}")
            return {"error": "Budget should be a valid number."}

        quiz_score = user['quiz_score']
        difficulty_level = user.get('preferred_difficulty', 'Beginner')  # Fetch user's preferred difficulty level
        preferred_platform = user.get('preferred_platform', 'udemy')  # Default to Udemy if not set

        logging.info(f"Fetching AI recommendations for: {specialization} with budget {budget}, difficulty: {difficulty_level}, platform: {preferred_platform}")

        # AI generates personalized course recommendations
        ai_response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"""
                Recommend the best 3 online courses for a {user['education_level']} student specializing in {specialization}.
                The student has a quiz score of {quiz_score}/10 and a budget of ${budget}.
                Their preferred difficulty level is {difficulty_level}.
                Their preferred platform is {preferred_platform}.
                Return a **STRICT JSON FORMAT ONLY** containing an array of exactly 3 objects where each object has:
                - "course_name": Name of the course
                - "platform": Udemy, Coursera, or YouTube
                - "price": Price of the course (0 if free)
                - "rating": Course rating out of 5
                - "difficulty_level": Beginner, Intermediate, or Advanced
                - "link": Direct link to the course

                No extra text or explanation. Just return 3 courses in a valid JSON array.
                """
            }],
            model="llama-3.3-70b-versatile",
        )

        ai_text_response = ai_response.choices[0].message.content.strip()

        logging.info(f"AI Response Before Parsing: {ai_text_response}")

        try:
            ai_recommendations = json.loads(ai_text_response)
        except json.JSONDecodeError:
            cleaned_json = clean_json_response(ai_text_response)
            try:
                ai_recommendations = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                logging.error(f"JSON Parsing Failed: {str(e)}")
                return {"error": "AI response was not in proper JSON format.", "raw_response": cleaned_json}

        if not isinstance(ai_recommendations, list) or len(ai_recommendations) == 0:
            logging.warning("AI returned an empty or invalid course list.")
            return {"error": "AI did not return valid course recommendations."}

        # Fetch real-world courses from Udemy, Coursera, and YouTube
        real_courses = fetch_courses(specialization, preferred_platform, budget)

        # Match top 3 best courses using embeddings and user preferences
        matched_courses = match_courses(user.get("embedding", []), difficulty_level) if "embedding" in user else []

        # Apply budget-based filtering and rank courses by difficulty
        try:
            filtered_courses = {
                "udemy": [
                    course for course in real_courses.get("udemy", [])
                    if "price" in course and isinstance(course["price"], (int, float)) and float(course["price"]) <= budget
                ][:3],
                "coursera": real_courses.get("coursera", [])[:3],
                "youtube": real_courses.get("youtube", [])[:3]
            }
        except Exception as e:
            logging.error(f"Error filtering courses by price: {str(e)}")
            logging.error(traceback.format_exc())
            return {"error": f"Error while filtering courses: {str(e)}"}

        # Sort filtered courses by user's preferred difficulty level safely
        for platform, courses in filtered_courses.items():
            filtered_courses[platform] = sorted(
                courses,
                key=lambda x: x.get('difficulty_level', 'Beginner') == difficulty_level,
                reverse=True
            )[:3]

        return {
            "ai_recommendations": ai_recommendations,
            "matched_courses": matched_courses if matched_courses else "No matched courses found",
            "real_courses": filtered_courses
        }

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        logging.error(traceback.format_exc())  
        return {"error": f"Internal Server Error: {str(e)}"}
