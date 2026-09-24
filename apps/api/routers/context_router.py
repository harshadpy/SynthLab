from datetime import datetime, timezone
from fastapi import APIRouter
from apps.api.core.config import settings

router = APIRouter(prefix="/context", tags=["context"])

@router.get("")
async def get_context():
    """
    Returns the persistent feature updates and architecture context from the root context.md.
    """
    context_file = settings.BASE_DIR / "docs" / "context.md"
    if not context_file.exists():
        context_file = settings.BASE_DIR / "context.md"
    content = context_file.read_text(encoding="utf-8") if context_file.exists() else ""
    return {
        "content": content,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
