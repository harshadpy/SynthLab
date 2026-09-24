from typing import List
from fastapi import APIRouter, Query, HTTPException
from apps.api.services.arxiv_service import arxiv_service
from apps.api.schemas.arxiv import ArXivSearchResponse, ArXivPaperItem

router = APIRouter(prefix="/arxiv", tags=["arxiv"])

@router.get("/trending", response_model=List[ArXivPaperItem])
async def get_trending_papers(limit: int = Query(10, ge=1, le=25)):
    return await arxiv_service.get_trending(limit=limit)

@router.get("/search", response_model=ArXivSearchResponse)
async def search_arxiv(
    q: str = Query(..., min_length=1, description="Search query"),
    max_results: int = Query(15, ge=1, le=50),
    sort_by: str = Query("relevance", pattern="^(relevance|date)$")
):
    return await arxiv_service.search(query=q, max_results=max_results, sort_by=sort_by)

@router.get("/papers/{arxiv_id}", response_model=ArXivPaperItem)
async def get_arxiv_paper(arxiv_id: str):
    paper = await arxiv_service.get_paper(arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {arxiv_id} not found")
    return paper
