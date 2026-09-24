from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class EvaluationExampleCreate(BaseModel):
    question: str
    ground_truth: Optional[str] = None
    relevant_paper_ids: List[str] = []
    relevant_chunk_ids: List[str] = []
    difficulty: str = "medium"
    question_type: str = "synthesis"

class EvaluationDatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    corpus_id: Optional[str] = None
    examples: List[EvaluationExampleCreate] = []

class EvaluationExperimentRunRequest(BaseModel):
    dataset_id: str
    architectures: List[str] = ["Hybrid", "Hierarchical", "GraphRAG", "Agentic", "Adaptive"]
    model_version: str = "gpt-4o"
