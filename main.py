from fastapi import FastAPI
from routes import user, quiz, recommendations, agents, translation

app = FastAPI(title="VisionX AI Backend")

app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(agents.router, prefix="/agents", tags=["Agents"])
app.include_router(translation.router, prefix="/translation", tags=["Translation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
