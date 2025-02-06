from config import groq_client
import logging

logging.basicConfig(level=logging.INFO)

def run_agents(specialization, quiz_score, required_level):
    """AI Agent refines recommendations based on user's level, learning style, and budget."""
    logging.info(f"🤖 Running AI Agents for {specialization} (Level: {required_level})")

    ai_response = groq_client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": f"""
            Act as an AI education expert. Recommend 5 online courses for a student specializing in {specialization}.
            - The student has a quiz score of {quiz_score}/10.
            - The required difficulty level is {required_level}.
            - Courses should include Udemy, Coursera, and YouTube.
            - Ensure each course has a valid link.
            - Format the response as a JSON array of objects.
            """
        }],
        model="llama-3.3-70b-versatile",
    )

    try:
        recommendations = eval(ai_response.choices[0].message.content.strip())
        return recommendations if isinstance(recommendations, list) else []
    except Exception as e:
        logging.error(f"❌ AI Agent Error: {e}")
        return []
