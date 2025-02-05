import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "visionx")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from groq import Groq
groq_client = Groq(api_key=GROQ_API_KEY)
