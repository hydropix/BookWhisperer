from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.api.v1 import books, health, chapters, jobs, audio

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BookWhisperer - Convert EPUB/TXT books to audiobooks using LLM and TTS",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=f"{settings.API_V1_PREFIX}/health", tags=["health"])
app.include_router(books.router, prefix=f"{settings.API_V1_PREFIX}/books", tags=["books"])
app.include_router(chapters.router, prefix=f"{settings.API_V1_PREFIX}/books", tags=["chapters"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["jobs"])
app.include_router(audio.router, prefix=f"{settings.API_V1_PREFIX}", tags=["audio"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to BookWhisperer API",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
