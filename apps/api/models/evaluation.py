import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from apps.api.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    corpus_id = Column(String, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0")
    item_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    examples = relationship("EvaluationExample", back_populates="dataset", cascade="all, delete-orphan")
    experiments = relationship("EvaluationExperiment", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationExample(Base):
    __tablename__ = "evaluation_examples"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    ground_truth = Column(Text, nullable=True)
    relevant_paper_ids = Column(JSON, default=list)
    relevant_chunk_ids = Column(JSON, default=list)
    difficulty = Column(String(50), default="medium")  # easy, medium, hard
    question_type = Column(String(50), default="synthesis")  # factual, multi-hop, synthesis, comparative
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("EvaluationDataset", back_populates="examples")


class EvaluationExperiment(Base):
    __tablename__ = "evaluation_experiments"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False)
    corpus_id = Column(String, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    git_commit = Column(String(64), default="main-e9b42")
    corpus_version = Column(String(50), default="v1.0")
    model_version = Column(String(100), default="gpt-4o")
    embedding_model = Column(String(100), default="text-embedding-3-large")
    status = Column(String(50), default="running")  # running, completed, failed
    results = Column(JSON, default=dict)  # architecture -> metrics dict
    langsmith_project_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("EvaluationDataset", back_populates="experiments")
