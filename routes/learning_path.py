from fastapi import APIRouter, Query
from config import groq_client
from utils.email_service import send_email  # ✅ Ensure correct import
import json
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)

@router.post("/generate_learning_path/")
def generate_learning_path(
    user_id: str,
    goal: str,
    send_email: bool = False,
    user_email: str = Query(None, title="User Email (Required if send_email=true)")
):
    """ 
    1️⃣ Identifies necessary skills 
    2️⃣ Generates a 5-question quiz 
    3️⃣ Recommends a structured learning path 
    4️⃣ Optionally emails the learning path to the user 
    """

    # ✅ 1. Identify Required Skills
    logging.info(f"🔍 Identifying required skills for {goal}...")

    skills_prompt = f"""
    List the most important skills required to achieve this goal: {goal}.
    Format the response STRICTLY as a JSON array with no extra text.
    Example: ["Skill 1", "Skill 2", "Skill 3"]
    """
    
    skills_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": skills_prompt}],
        model="llama-3.3-70b-versatile",
    )

    try:
        raw_skills = skills_response.choices[0].message.content.strip()
        logging.info(f"🛠 AI Response (Raw Skills): {raw_skills}")
        required_skills = json.loads(raw_skills)  # ✅ Ensures correct JSON format
    except json.JSONDecodeError as e:
        logging.error(f"❌ Skill Extraction Failed: {e}")
        return {"error": "Failed to identify required skills.", "raw_response": raw_skills}

    # ✅ 2. Generate a Quiz
    logging.info(f"📝 Generating quiz for skills: {required_skills}...")

    quiz_prompt = f"""
    Generate a 5-question multiple-choice quiz to assess knowledge in these skills: {', '.join(required_skills)}.
    Format the response STRICTLY as a JSON array with no extra text.
    Each object should have:
    - "question": The question text
    - "options": A list of 4 multiple-choice answers
    - "correct_answer": The correct option (e.g., "A", "B", "C", or "D")
    """

    quiz_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": quiz_prompt}],
        model="llama-3.3-70b-versatile",
    )

    try:
        raw_quiz = quiz_response.choices[0].message.content.strip()
        logging.info(f"📝 AI Response (Raw Quiz): {raw_quiz}")
        quiz_questions = json.loads(raw_quiz)
    except json.JSONDecodeError as e:
        logging.error(f"❌ Quiz Generation Failed: {e}")
        return {"error": "Failed to generate quiz.", "raw_response": raw_quiz}

    # ✅ 3. Recommend Learning Path
    logging.info(f"📚 Creating learning path for {goal}...")

    learning_path_prompt = f"""
    Recommend a structured learning path for a beginner in {goal}.
    Use these skills: {', '.join(required_skills)}.
    Format the response STRICTLY as a JSON array with no extra text.
    Example: ["Step 1", "Step 2", "Step 3"]
    """

    learning_path_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": learning_path_prompt}],
        model="llama-3.3-70b-versatile",
    )

    try:
        raw_learning_path = learning_path_response.choices[0].message.content.strip()
        logging.info(f"📚 AI Response (Raw Learning Path): {raw_learning_path}")
        learning_path = json.loads(raw_learning_path)
    except json.JSONDecodeError as e:
        logging.error(f"❌ Learning Path Generation Failed: {e}")
        return {"error": "Failed to generate learning path.", "raw_response": raw_learning_path}

    # ✅ 4. Email the Learning Path (if requested)
    email_status = "Email not requested."
    if send_email and user_email:
        logging.info(f"📩 Sending learning path to {user_email}...")
        email_sent = send_learning_path_email(user_email, goal, required_skills, quiz_questions, learning_path)
        email_status = "Email sent successfully!" if email_sent else "Failed to send email."

    return {
        "goal": goal,
        "required_skills": required_skills,
        "quiz": quiz_questions,
        "learning_path": learning_path,
        "email_status": email_status
    }

def send_learning_path_email(to_email, goal, required_skills, quiz, learning_path):
    """ ✅ Sends structured email with the learning path """
    logging.info(f"📩 Preparing email for {to_email}...")

    subject = f"🎯 Your AI-Powered Learning Path for {goal}"

    quiz_html = "".join([
        f"<li><b>{q['question']}</b><br>A) {q['options'][0]} | B) {q['options'][1]} | C) {q['options'][2]} | D) {q['options'][3]}</li>"
        for q in quiz
    ])

    path_html = "".join([f"<li>{step}</li>" for step in learning_path])

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="color: #007bff; text-align: center;">🚀 Your AI-Powered Learning Path for {goal}</h2>
        <p><b>Required Skills:</b> {', '.join(required_skills)}</p>
        <h3>📝 Your Quiz</h3>
        <ul>{quiz_html}</ul>
        <h3>📚 Recommended Learning Path</h3>
        <ul>{path_html}</ul>
        <hr style="border: 0; height: 1px; background: #ddd;">
        <p style="text-align: center;">Happy Learning! 🚀</p>
        <p style="text-align: center;"><b>Best Regards,<br>Intellica Team</b></p>
    </div>
    """

    email_sent = send_email(to_email, subject, html_content)

    if email_sent:
        logging.info(f"✅ Email sent successfully to {to_email}")
    else:
        logging.error(f"❌ Email failed to send to {to_email}")

    return email_sent
