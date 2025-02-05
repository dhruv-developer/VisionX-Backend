from fastapi import APIRouter
from config import groq_client
from database import users_collection
from bson import ObjectId  # Handle MongoDB IDs

router = APIRouter()

# Store quizzes temporarily
user_quizzes = {}

@router.post("/start_quiz/")
def start_quiz(user_id: str):
    """Start quiz and generate the first question."""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"error": "User not found"}

        # AI generates quiz questions based on user's specialization
        quiz_response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Generate a 10-question multiple-choice quiz on prerequisites for {user['specialization']}. "
                           f"Each question must be formatted as:\n"
                           f"Question: <question_text>\n"
                           f"A) <option_1>\n"
                           f"B) <option_2>\n"
                           f"C) <option_3>\n"
                           f"D) <option_4>\n"
                           f"Provide only the quiz questions and options, without explanations."
            }],
            model="llama-3.3-70b-versatile",
        )

        # Properly parse the questions by separating them correctly
        questions = [q.strip() for q in quiz_response.choices[0].message.content.split("\n\n") if q.strip()]

        # Ensure exactly 10 questions are extracted
        if len(questions) < 10:
            return {"error": "AI did not generate enough questions. Please restart quiz."}

        user_quizzes[user_id] = {
            "questions": questions[:10],  # Store only 10 questions
            "current_question": 0,
            "score": 0,
            "total_questions": 10,
        }

        return {
            "question": user_quizzes[user_id]["questions"][0],
            "question_number": 1
        }

    except Exception as e:
        return {"error": str(e)}

@router.post("/answer_question/")
def answer_question(user_id: str, answer: str):
    """Process user's answer and return the next question."""
    try:
        if user_id not in user_quizzes:
            return {"error": "Quiz not started. Call /start_quiz/ first."}

        quiz = user_quizzes[user_id]
        current_question = quiz["current_question"]

        # AI Evaluates if the user's answer is correct
        eval_response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Given the multiple-choice question: {quiz['questions'][current_question]}, "
                           f"what is the correct answer? Reply with just the correct option (A, B, C, or D)."
            }],
            model="llama-3.3-70b-versatile",
        )

        correct_answer = eval_response.choices[0].message.content.strip().upper()

        # Check if user answer matches AI's correct answer
        if answer.strip().upper() == correct_answer:
            quiz["score"] += 1  # Increment score if correct

        # Move to next question
        quiz["current_question"] += 1

        if quiz["current_question"] >= quiz["total_questions"]:
            # Quiz completed, save score
            final_score = quiz["score"]
            users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"quiz_score": final_score}})
            del user_quizzes[user_id]  # Cleanup
            return {"message": "Quiz completed!", "final_score": final_score}

        # Return next question
        return {
            "question": quiz["questions"][quiz["current_question"]],
            "question_number": quiz["current_question"] + 1
        }

    except Exception as e:
        return {"error": str(e)}
