export interface ArXivPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  categories: string[];
  published_date: string;
  pdf_url: string;
}

export interface Paper {
  id: string;
  corpus_id: string;
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract?: string;
  categories: string[];
  published_date?: string;
  pdf_url?: string;
  status: 'queued' | 'downloading' | 'parsing' | 'chunking' | 'indexed' | 'failed';
  status_message?: string;
  page_count: number;
  chunk_count: number;
  created_at: string;
}

export interface Corpus {
  id: string;
  name: string;
  description?: string;
  query?: string;
  status: string;
  paper_count: number;
  page_count: number;
  chunk_count: number;
  categories: string[];
  created_at: string;
  updated_at: string;
  papers: Paper[];
}

export interface Citation {
  chunk_id: string;
  paper_id: string;
  arxiv_id: string;
  paper_title: string;
  page_number: number;
  section_name?: string;
  content: string;
  similarity_score: number;
  bm25_score: number;
  reranker_score?: number;
  rank: number;
  token_range?: string;
  attention_depth?: 'start' | 'middle' | 'end';
  strategy_metadata?: Record<string, any>;
}

export interface AnswerResult {
  answer: string;
  citations: Citation[];
  strategy: string;
  model: string;
  latency_ms: number;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  token_usage: {
    input: number;
    output: number;
    total: number;
  };
  trace_id?: string;
  intermediate_steps?: any[];
}

export interface ArchitectureInfo {
  name: string;
  tagline: string;
  description: string;
  strengths: string[];
  tradeoffs: string[];
  retrieval_strategy: string;
}

export interface MetricSummary {
  architecture: string;
  correctness: number;
  faithfulness: number;
  recall_at_k: number;
  latency_ms: number;
  tokens: number;
  estimated_cost: string;
  questions_evaluated: number;
  // Extended IR metrics
  precision_at_k?: number;
  mrr?: number;
  ndcg?: number;
  hit_rate?: number;
  citation_correctness?: number;
}
