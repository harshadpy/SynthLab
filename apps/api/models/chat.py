import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from apps.api.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    corpus_id = Column(String, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), default="New Research Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    corpus = relationship("Corpus", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    run_id = Column(String, ForeignKey("rag_runs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    run = relationship("RAGRun", back_populates="message", uselist=False)


class RAGRun(Base):
    __tablename__ = "rag_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    corpus_id = Column(String, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False)
    strategy = Column(String(50), nullable=False)  # Hybrid, Hierarchical, GraphRAG, Agentic, Adaptive
    query = Column(Text, nullable=False)
    model = Column(String(100), default="gpt-4o")
    latency_ms = Column(Integer, default=0)
    retrieval_latency_ms = Column(Integer, default=0)
    generation_latency_ms = Column(Integer, default=0)
    token_usage = Column(JSON, default=dict)  # input, output, total
    citations = Column(JSON, default=list)  # list of citation objects with chunk_id, paper_id, scores
    intermediate_steps = Column(JSON, default=list)  # for Agentic / Adaptive routing steps
    trace_id = Column(String(255), nullable=True)  # LangSmith trace ID
    config = Column(JSON, default=dict)  # top_k, reranker, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    corpus = relationship("Corpus", back_populates="runs")
    message = relationship("Message", back_populates="run")
    feedback = relationship("Feedback", back_populates="run", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("rag_runs.id", ondelete="CASCADE"), nullable=False)
    rating = Column(String(50), nullable=False)  # helpful, not_helpful, correct, incorrect, missing_evidence
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("RAGRun", back_populates="feedback")
