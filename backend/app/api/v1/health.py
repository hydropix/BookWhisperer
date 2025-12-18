from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx

from app.database import get_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("")
async def health_check():
    """
    Basic health check endpoint

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "bookwhisperer-api",
        "version": "0.1.0"
    }


@router.get("/db")
async def health_check_db(db: Session = Depends(get_db)):
    """
    Check database connection

    Args:
        db: Database session

    Returns:
        dict: Database health status
    """
    try:
        # Execute simple query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "component": "database",
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "component": "database",
            "message": f"Database connection failed: {str(e)}"
        }


@router.get("/ollama")
async def health_check_ollama():
    """
    Check Ollama service connection

    Returns:
        dict: Ollama health status
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name") for model in data.get("models", [])]
                return {
                    "status": "healthy",
                    "component": "ollama",
                    "message": "Ollama service is running",
                    "available_models": models
                }
            else:
                return {
                    "status": "unhealthy",
                    "component": "ollama",
                    "message": f"Ollama service returned status {response.status_code}"
                }
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "component": "ollama",
            "message": "Ollama service timeout"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "component": "ollama",
            "message": f"Ollama service unavailable: {str(e)}"
        }


@router.get("/tts")
async def health_check_tts():
    """
    Check Chatterbox TTS service connection

    Returns:
        dict: TTS health status
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Chatterbox /voices endpoint for availability
            response = await client.get(f"{settings.CHATTERBOX_URL}/voices")
            if response.status_code == 200:
                data = response.json()
                voices_count = len(data) if isinstance(data, list) else 0
                return {
                    "status": "healthy",
                    "component": "chatterbox_tts",
                    "message": "Chatterbox TTS service is running",
                    "voices_count": voices_count
                }
            else:
                return {
                    "status": "unhealthy",
                    "component": "chatterbox_tts",
                    "message": f"Chatterbox TTS service returned status {response.status_code}"
                }
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "component": "chatterbox_tts",
            "message": "Chatterbox TTS service timeout"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "component": "chatterbox_tts",
            "message": f"Chatterbox TTS service unavailable: {str(e)}"
        }


@router.get("/all")
async def health_check_all(db: Session = Depends(get_db)):
    """
    Check all services

    Args:
        db: Database session

    Returns:
        dict: Complete health status
    """
    # Check database
    db_health = await health_check_db(db)

    # Check Ollama
    ollama_health = await health_check_ollama()

    # Check TTS
    tts_health = await health_check_tts()

    # Determine overall status
    all_healthy = all([
        db_health.get("status") == "healthy",
        ollama_health.get("status") == "healthy",
        tts_health.get("status") == "healthy"
    ])

    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": {
            "database": db_health,
            "ollama": ollama_health,
            "tts": tts_health
        }
    }
