import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from apps.api.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Corpus(Base):
    __tablename__ = "corpora"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    query = Column(String(512), nullable=True)
    status = Column(String(50), default="ready")  # ready, processing, error
    paper_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    categories = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    papers = relationship("Paper", back_populates="corpus", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="corpus", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="corpus", cascade="all, delete-orphan")
    runs = relationship("RAGRun", back_populates="corpus", cascade="all, delete-orphan")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, default=generate_uuid)
    corpus_id = Column(String, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False)
    arxiv_id = Column(String(64), nullable=False, index=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON, default=list)
    abstract = Column(Text, nullable=True)
    categories = Column(JSON, default=list)
    published_date = Column(String(50), nullable=True)
    pdf_url = Column(String(512), nullable=True)
    local_pdf_path = Column(String(512), nullable=True)
    status = Column(String(50), default="queued")  # queued, downloading, parsing, chunking, indexed, failed
    status_message = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    corpus = relationship("Corpus", back_populates="papers")
    chunks = relationship("Chunk", back_populates="paper", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    corpus_id = Column(String, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(String, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    arxiv_id = Column(String(64), nullable=False)
    page_number = Column(Integer, nullable=False)
    section_name = Column(String(255), nullable=True)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    parent_chunk_id = Column(String, nullable=True)  # For hierarchical RAG parent resolution
    chunk_type = Column(String(50), default="child")  # child, parent, summary
    text_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    corpus = relationship("Corpus", back_populates="chunks")
    paper = relationship("Paper", back_populates="chunks")
