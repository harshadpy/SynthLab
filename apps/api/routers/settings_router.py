import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from apps.api.core.config import settings
from apps.api.core.langsmith import langsmith_tracker

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsPayload(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    default_chat_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    langchain_tracing_v2: Optional[bool] = None
    langchain_endpoint: Optional[str] = None
    langchain_api_key: Optional[str] = None
    langchain_project: Optional[str] = None

def mask_key(k: str) -> str:
    if not k:
        return ""
    if len(k) <= 8:
        return "****"
    return k[:3] + "..." + k[-4:]

@router.get("")
async def get_settings():
    return {
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "openai_api_key_masked": mask_key(settings.OPENAI_API_KEY),
        "anthropic_api_key_configured": bool(settings.ANTHROPIC_API_KEY),
        "anthropic_api_key_masked": mask_key(settings.ANTHROPIC_API_KEY),
        "cohere_api_key_configured": bool(settings.COHERE_API_KEY),
        "cohere_api_key_masked": mask_key(settings.COHERE_API_KEY),
        "default_chat_model": settings.DEFAULT_CHAT_MODEL,
        "default_embedding_model": settings.DEFAULT_EMBEDDING_MODEL,
        "langchain_tracing_v2": settings.LANGCHAIN_TRACING_V2.lower() in ("true", "1"),
        "langchain_endpoint": settings.LANGCHAIN_ENDPOINT,
        "langchain_api_key_configured": bool(settings.LANGCHAIN_API_KEY),
        "langchain_api_key_masked": mask_key(settings.LANGCHAIN_API_KEY),
        "langchain_project": settings.LANGCHAIN_PROJECT,
    }

@router.post("")
async def update_settings(payload: SettingsPayload):
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key
        os.environ["OPENAI_API_KEY"] = payload.openai_api_key
    if payload.anthropic_api_key is not None:
        settings.ANTHROPIC_API_KEY = payload.anthropic_api_key
        os.environ["ANTHROPIC_API_KEY"] = payload.anthropic_api_key
    if payload.cohere_api_key is not None:
        settings.COHERE_API_KEY = payload.cohere_api_key
        os.environ["COHERE_API_KEY"] = payload.cohere_api_key
    if payload.default_chat_model:
        settings.DEFAULT_CHAT_MODEL = payload.default_chat_model
    if payload.default_embedding_model:
        settings.DEFAULT_EMBEDDING_MODEL = payload.default_embedding_model
    if payload.langchain_tracing_v2 is not None:
        settings.LANGCHAIN_TRACING_V2 = "true" if payload.langchain_tracing_v2 else "false"
        os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    if payload.langchain_endpoint:
        settings.LANGCHAIN_ENDPOINT = payload.langchain_endpoint
        os.environ["LANGCHAIN_ENDPOINT"] = payload.langchain_endpoint
    if payload.langchain_api_key is not None:
        settings.LANGCHAIN_API_KEY = payload.langchain_api_key
        os.environ["LANGCHAIN_API_KEY"] = payload.langchain_api_key
    if payload.langchain_project:
        settings.LANGCHAIN_PROJECT = payload.langchain_project
        os.environ["LANGCHAIN_PROJECT"] = payload.langchain_project

    return {"status": "success", "message": "Settings updated successfully"}
