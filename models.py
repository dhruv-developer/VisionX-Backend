from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    name: str
    education_level: str
    specialization: str
    budget: str
    preferred_language: Optional[str] = "English"
    embedding: Optional[List[float]] = None  # Vector embeddings for FAISS matching

class QuizResult(BaseModel):
    user_id: str
    score: int

class Course(BaseModel):
    title: str
    platform: str
    url: str
    difficulty: Optional[str] = "Beginner"
    language: Optional[str] = "English"
    embedding: Optional[List[float]] = None  # Vector embeddings for FAISS matching
