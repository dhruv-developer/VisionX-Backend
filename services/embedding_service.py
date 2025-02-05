import faiss
import numpy as np
import logging
from database import courses_collection

DIMENSION = 512  # Ensure this matches the actual embedding size
index = faiss.IndexFlatL2(DIMENSION)  # FAISS index setup

# Enable logging
logging.basicConfig(level=logging.INFO)

def load_embeddings():
    try:
        courses = list(courses_collection.find({}, {"_id": 1, "embedding": 1, "rating": 1, "difficulty_level": 1}))

        valid_courses = [c for c in courses if "embedding" in c and isinstance(c["embedding"], list)]
        
        if not valid_courses:
            logging.warning("No valid embeddings found in the database.")
            return

        embeddings = np.array([c["embedding"] for c in valid_courses], dtype=np.float32)

        if embeddings.shape[1] != DIMENSION:
            logging.error(f"Embedding dimension mismatch: Expected {DIMENSION}, but got {embeddings.shape[1]}")
            return

        index.add(embeddings)
        logging.info(f"Loaded {len(valid_courses)} embeddings into FAISS.")

    except Exception as e:
        logging.error(f"Error loading embeddings into FAISS: {str(e)}")

def match_courses(user_embedding, preferred_difficulty):
    try:
        if index.ntotal == 0:
            logging.warning("FAISS index is empty. No embeddings available for search.")
            return []

        user_embedding = np.array(user_embedding, dtype=np.float32).reshape(1, -1)

        if user_embedding.shape[1] != DIMENSION:
            logging.error(f"Query vector dimension mismatch: Expected {DIMENSION}, but got {user_embedding.shape[1]}")
            return []

        _, indices = index.search(user_embedding, 5)

        matched_courses = []
        for i in indices[0]:
            course = courses_collection.find_one({"_id": i})
            if course and course["difficulty_level"] == preferred_difficulty:  # Filter based on difficulty
                matched_courses.append(course)

        matched_courses = sorted(matched_courses, key=lambda x: x.get("rating", 0), reverse=True)[:3]

        logging.info(f"Returning top {len(matched_courses)} best-matched courses.")
        return matched_courses

    except Exception as e:
        logging.error(f"Error in FAISS search: {str(e)}")
        return []
