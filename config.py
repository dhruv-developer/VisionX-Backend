import os
from pymongo import MongoClient
from groq import Groq

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://dhruvdawar11022006:dd110206@cluster0.gohdq.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "intellica_courses")  # ✅ Updated DB Name

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Groq AI Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# SMTP Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "intellica2025@gmail.com")  
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "xqomgnybmcnjntbz")  
