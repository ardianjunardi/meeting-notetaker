from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.models.database import init_db
from app.routes import dashboard, auth, meetings

# Create app
app = FastAPI(
    title="Meeting Notetaker",
    description="Bot joins Google Meet, captures audio, transcribes, and generates meeting minutes with LLM",
    version="1.0.0",
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()
    static_dir = Path("app/static")
    static_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = Path("audio_recordings")
    audio_dir.mkdir(parents=True, exist_ok=True)


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(meetings.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
