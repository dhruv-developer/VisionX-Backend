from pymongo import MongoClient
from groq import Groq

# ✅ MongoDB Connection with SSL Fix (Hardcoded)
MONGO_URI = "mongodb+srv://dhruvdawar11022006:dd110206@cluster0.gohdq.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true&tlsInsecure=true"
DB_NAME = "intellica_courses"

try:
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True, tlsInsecure=True)
    db = client[DB_NAME]
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")

# ✅ Groq AI Key (Hardcoded)
GROQ_API_KEY = "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"  # Ensure this is valid
groq_client = Groq(api_key=GROQ_API_KEY)

# ✅ SMTP Email Configuration (Hardcoded)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "intellica2025@gmail.com"
SMTP_PASSWORD = "xqomgnybmcnjntbz"  # ⚠️ Make sure this is an **App Password**, NOT your real email password
