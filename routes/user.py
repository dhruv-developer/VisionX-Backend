from fastapi import APIRouter
from models import UserProfile
from database import users_collection
from bson import ObjectId

router = APIRouter()

@router.post("/register/")
def register_user(user: UserProfile):
    user_dict = user.dict()
    result = users_collection.insert_one(user_dict)
    return {"message": "User Registered", "user_id": str(result.inserted_id)}

@router.post("/set_preferences/")
def set_preferences(user_id: str, preferred_difficulty: str, preferred_platform: str, learning_style: str):
    """
    Allows the user to update preferences such as difficulty level, preferred platform, and learning style.
    """
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "preferred_difficulty": preferred_difficulty,
            "preferred_platform": preferred_platform,
            "learning_style": learning_style
        }}
    )
    return {"message": "Preferences updated"}

@router.post("/set_budget/")
def set_budget(user_id: str, budget: float):
    """
    Allows the user to set their budget for courses.
    """
    users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"budget": budget}})
    return {"message": "Budget updated", "budget": budget}
