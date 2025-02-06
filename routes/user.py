from fastapi import APIRouter
from models import UserProfile
from database import db
from bson import ObjectId
from utils.email_service import generate_otp, send_otp_email

router = APIRouter()
users_collection = db["users"]

@router.post("/register/")
def register_user(user: UserProfile):
    otp = generate_otp()
    send_otp_email(user.email, otp)  # ✅ Send OTP via email
    user_dict = user.dict()
    user_dict["otp"] = otp  # ✅ Store OTP temporarily
    result = users_collection.insert_one(user_dict)
    return {"message": "OTP sent to email. Verify to complete registration.", "user_id": str(result.inserted_id)}

@router.post("/verify_otp/")
def verify_otp(user_id: str, otp: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or user["otp"] != otp:
        return {"error": "Invalid OTP"}
    users_collection.update_one({"_id": ObjectId(user_id)}, {"$unset": {"otp": ""}})
    return {"message": "Registration successful!"}
