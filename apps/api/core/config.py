import os
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Normalize LangSmith / LangChain env variables
tracing_enabled = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false")).lower() in ("true", "1")
langsmith_key = os.getenv("LANGSMITH_API_KEY", os.getenv("LANGCHAIN_API_KEY", ""))
langsmith_project = os.getenv("LANGSMITH_PROJECT", os.getenv("LANGCHAIN_PROJECT", "raglab")).strip('"').strip("'")
langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"))

if tracing_enabled and langsmith_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = langsmith_key
    os.environ["LANGCHAIN_PROJECT"] = langsmith_project
    os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
INDEX_DIR = DATA_DIR / "indices"

PDF_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")  # type: ignore
    PROJECT_NAME: str = "RAGLab"
    VERSION: str = "1.4.0"
    API_V1_STR: str = "/api"
    
    # Storage paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    PDF_DIR: Path = PDF_DIR
    INDEX_DIR: Path = INDEX_DIR
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'arxiv_rag.db'}"
    
    # LLM & Embedding Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    
    # Default Models
    DEFAULT_CHAT_MODEL: str = os.getenv("DEFAULT_CHAT_MODEL", "gpt-5.6-luna")
    DEFAULT_EMBEDDING_MODEL: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # LangSmith Observability
    LANGCHAIN_TRACING_V2: str = "true" if tracing_enabled else "false"
    LANGCHAIN_ENDPOINT: str = langsmith_endpoint
    LANGCHAIN_API_KEY: str = langsmith_key
    LANGCHAIN_PROJECT: str = langsmith_project

    # Neo4j Graph Database
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

settings = Settings()
