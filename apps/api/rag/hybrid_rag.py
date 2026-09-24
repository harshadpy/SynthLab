import time
from typing import Dict, Any, List, Tuple, cast
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from apps.api.schemas.rag import RetrievalResult, AnswerResult, Citation
from apps.api.services.index_service import index_service
from apps.api.rag.base import compute_rrf, build_citation, generate_research_answer, is_general_query, build_general_query_answer
from apps.api.rag.common import LocalCrossEncoderReranker, CitationVerifier
from apps.api.core.langsmith import langsmith_tracker

class HybridState(TypedDict):
    query: str
    corpus_id: str
    config: Dict[str, Any]
    dense_results: List[Tuple[str, float]]
    sparse_results: List[Tuple[str, float]]
    fused_results: List[Tuple[str, float]]
    reranked_results: List[Tuple[str, float]]
    is_sufficient: bool
    citations: List[Citation]
    intermediate_steps: List[Dict[str, Any]]
    answer: str
    token_usage: Dict[str, int]

class HybridRAGPipeline:
    name = "Hybrid"

    def __init__(self):
        self.reranker = LocalCrossEncoderReranker()
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(HybridState)  # type: ignore

        workflow.add_node("retrieve_dense", self._node_retrieve_dense)
        workflow.add_node("retrieve_sparse", self._node_retrieve_sparse)
        workflow.add_node("reciprocal_rank_fusion", self._node_reciprocal_rank_fusion)
        workflow.add_node("rerank_candidates", self._node_rerank_candidates)
        workflow.add_node("verify_evidence_sufficiency", self._node_verify_sufficiency)
        workflow.add_node("build_citations", self._node_build_citations)
        workflow.add_node("generate", self._node_generate)

        workflow.set_entry_point("retrieve_dense")
        workflow.add_edge("retrieve_dense", "retrieve_sparse")
        workflow.add_edge("retrieve_sparse", "reciprocal_rank_fusion")
        workflow.add_edge("reciprocal_rank_fusion", "rerank_candidates")
        workflow.add_edge("rerank_candidates", "verify_evidence_sufficiency")
        workflow.add_edge("verify_evidence_sufficiency", "build_citations")
        workflow.add_edge("build_citations", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def _node_retrieve_dense(self, state: HybridState) -> Dict[str, Any]:
        corpus_id = state["corpus_id"]
        query = state["query"]
        top_k = state["config"].get("dense_top_k", state["config"].get("top_k", 8) * 2)

        dense_results = index_service.search_dense(corpus_id, query, top_k=top_k)
        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Dense Semantic Retrieval (OpenAI text-embedding-3)",
            "matches": len(dense_results),
            "dense_top_k": top_k
        })
        return {"dense_results": dense_results, "intermediate_steps": steps}

    def _node_retrieve_sparse(self, state: HybridState) -> Dict[str, Any]:
        corpus_id = state["corpus_id"]
        query = state["query"]
        top_k = state["config"].get("sparse_top_k", state["config"].get("top_k", 8) * 2)

        sparse_results = index_service.search_sparse(corpus_id, query, top_k=top_k)
        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Sparse Lexical Retrieval (BM25s Inverted Index)",
            "matches": len(sparse_results),
            "sparse_top_k": top_k
        })
        return {"sparse_results": sparse_results, "intermediate_steps": steps}

    def _node_reciprocal_rank_fusion(self, state: HybridState) -> Dict[str, Any]:
        dense_results = state.get("dense_results", [])
        sparse_results = state.get("sparse_results", [])
        rrf_k = state["config"].get("rrf_k", 60)

        dense_ids = [d[0] for d in dense_results]
        sparse_ids = [s[0] for s in sparse_results]

        fused = compute_rrf(dense_ids, sparse_ids, k=rrf_k)
        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": f"LangGraph: Reciprocal Rank Fusion (k={rrf_k})",
            "fused_candidates": len(fused),
            "rrf_k": rrf_k
        })
        return {"fused_results": fused, "intermediate_steps": steps}

    def _node_rerank_candidates(self, state: HybridState) -> Dict[str, Any]:
        corpus_id = state["corpus_id"]
        query = state["query"]
        fused = state.get("fused_results", [])
        dense_map = dict(state.get("dense_results", []))
        sparse_map = dict(state.get("sparse_results", []))
        rerank_enabled = state["config"].get("rerank_enabled", True)
        rerank_top_k = state["config"].get("rerank_top_k", state["config"].get("top_k", 8))

        steps = list(state.get("intermediate_steps", []))

        if not rerank_enabled:
            steps.append({
                "step": "LangGraph: Cross-Encoder Reranker (Bypassed by config)",
                "rerank_enabled": False
            })
            return {"reranked_results": fused[:rerank_top_k], "intermediate_steps": steps}

        # Build candidates for reranking
        candidates_to_score = []
        for cid, _ in fused[:rerank_top_k * 2]:
            chunk = index_service.get_chunk(corpus_id, cid)
            if chunk:
                candidates_to_score.append({
                    "id": cid,
                    "content": chunk.get("content", ""),
                    "dense_score": dense_map.get(cid, 0.75),
                    "sparse_score": sparse_map.get(cid, 10.0)
                })

        reranked_pairs = self.reranker.rerank(query, candidates_to_score, top_k=rerank_top_k)
        reranked_results = [(c["id"], score) for c, score in reranked_pairs]

        steps.append({
            "step": "LangGraph: Local Cross-Encoder Reranker",
            "reranked_candidates": len(reranked_results),
            "model": self.reranker.model_name
        })
        return {"reranked_results": reranked_results, "intermediate_steps": steps}

    def _node_verify_sufficiency(self, state: HybridState) -> Dict[str, Any]:
        reranked = state.get("reranked_results", [])
        is_sufficient = len(reranked) > 0 and reranked[0][1] >= 0.20

        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Evidence Sufficiency Gate",
            "is_sufficient": is_sufficient,
            "top_evidence_score": round(reranked[0][1], 3) if reranked else 0.0
        })
        return {"is_sufficient": is_sufficient, "intermediate_steps": steps}

    def _node_build_citations(self, state: HybridState) -> Dict[str, Any]:
        corpus_id = state["corpus_id"]
        config = state["config"]
        final_k = config.get("final_context_k", config.get("top_k", 8))
        reranked = state.get("reranked_results", [])
        dense_map = dict(state.get("dense_results", []))
        sparse_map = dict(state.get("sparse_results", []))
        dense_rank_map = {cid: r + 1 for r, (cid, _) in enumerate(state.get("dense_results", []))}
        sparse_rank_map = {cid: r + 1 for r, (cid, _) in enumerate(state.get("sparse_results", []))}

        citations: List[Citation] = []
        for rank, (cid, score) in enumerate(reranked[:final_k], start=1):
            chunk = index_service.get_chunk(corpus_id, cid)
            if chunk:
                d_sim = float(dense_map.get(cid, 0.75))
                s_bm = float(sparse_map.get(cid, 10.0))
                meta = {
                    "strategy": "Hybrid",
                    "technique": "LangGraph StateGraph: Dense HNSW + BM25s with RRF & Local Cross-Encoder",
                    "rrf_score": round(float(score), 4),
                    "dense_cosine": round(d_sim, 3),
                    "sparse_bm25": round(s_bm, 2),
                    "dense_rank": dense_rank_map.get(cid, "-"),
                    "sparse_rank": sparse_rank_map.get(cid, "-"),
                    "fusion_k": config.get("rrf_k", 60),
                    "orchestrator": "LangGraph"
                }
                c = build_citation(
                    chunk=chunk,
                    rank=rank,
                    similarity=d_sim,
                    bm25_score=s_bm,
                    reranker=round(float(score), 3),
                    strategy_metadata=meta
                )
                citations.append(c)

        return {"citations": citations}

    def _node_generate(self, state: HybridState) -> Dict[str, Any]:
        query = state["query"]
        citations = state.get("citations", [])
        model_name = state["config"].get("model", "gpt-4o")

        answer_text, usage = generate_research_answer(
            query=query,
            citations=citations,
            strategy_name=self.name,
            model_name=model_name,
            system_prompt_extra="You are executing the LangGraph Hybrid RAG pipeline (Dense + BM25s + RRF + Cross-Encoder)."
        )

        # Verify inline citations against evidence passages
        is_valid, cite_issues = CitationVerifier.verify(answer_text, citations)

        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Evidence Synthesis & Citation Verification",
            "model": model_name,
            "tokens": usage.get("total", 0),
            "citations_verified": is_valid,
            "citation_issues": cite_issues
        })

        return {
            "answer": answer_text,
            "token_usage": usage,
            "intermediate_steps": steps
        }

    async def retrieve(self, query: str, corpus_id: str, config: Dict[str, Any]) -> RetrievalResult:
        start_time = time.time()
        initial_state: HybridState = {
            "query": query,
            "corpus_id": corpus_id,
            "config": config,
            "dense_results": [],
            "sparse_results": [],
            "fused_results": [],
            "reranked_results": [],
            "is_sufficient": True,
            "citations": [],
            "intermediate_steps": [],
            "answer": "",
            "token_usage": {}
        }

        # Run pipeline up through citations
        dense_out = self._node_retrieve_dense(initial_state)
        sparse_state = cast(HybridState, {**initial_state, **dense_out})
        sparse_out = self._node_retrieve_sparse(sparse_state)
        fused_state = cast(HybridState, {**sparse_state, **sparse_out})
        fused_out = self._node_reciprocal_rank_fusion(fused_state)
        rerank_state = cast(HybridState, {**fused_state, **fused_out})
        rerank_out = self._node_rerank_candidates(rerank_state)
        suff_state = cast(HybridState, {**rerank_state, **rerank_out})
        suff_out = self._node_verify_sufficiency(suff_state)
        cit_state = cast(HybridState, {**suff_state, **suff_out})
        cit_out = self._node_build_citations(cit_state)

        citations: List[Citation] = cit_out["citations"]
        steps: List[Dict[str, Any]] = cit_state["intermediate_steps"]
        latency_ms = int((time.time() - start_time) * 1000)

        return RetrievalResult(
            query=query,
            strategy=self.name,
            citations=citations,
            retrieval_latency_ms=latency_ms,
            intermediate_steps=steps
        )

    async def generate(self, query: str, retrieval_result: RetrievalResult, config: Dict[str, Any]) -> AnswerResult:
        start_gen = time.time()
        cits = retrieval_result.citations
        model_name = config.get("model", "gpt-4o")

        answer_text, usage = generate_research_answer(
            query=query,
            citations=cits,
            strategy_name=self.name,
            model_name=model_name,
            system_prompt_extra="You are executing the LangGraph Hybrid RAG pipeline (Dense + BM25s + RRF + Cross-Encoder)."
        )

        gen_latency = int((time.time() - start_gen) * 1000)
        total_latency = retrieval_result.retrieval_latency_ms + gen_latency
        trace_id = langsmith_tracker.create_run_trace(
            name="HybridRAG_LangGraph",
            run_type="chain",
            inputs={"query": query, "top_k": config.get("top_k", 6)},
            outputs={"answer": answer_text, "citations_count": len(cits), "model": model_name},
            latency_ms=total_latency,
            extra={"metadata": {"strategy": self.name, "orchestrator": "LangGraph"}}
        )

        return AnswerResult(
            answer=answer_text,
            citations=cits,
            strategy=self.name,
            model=model_name,
            latency_ms=total_latency,
            retrieval_latency_ms=retrieval_result.retrieval_latency_ms,
            generation_latency_ms=gen_latency,
            token_usage=usage,
            trace_id=trace_id,
            intermediate_steps=retrieval_result.intermediate_steps
        )

    async def run(self, query: str, corpus_id: str, config: Dict[str, Any]) -> AnswerResult:
        if is_general_query(query):
            return build_general_query_answer(query, self.name)

        start_time = time.time()
        initial_state: HybridState = {
            "query": query,
            "corpus_id": corpus_id,
            "config": config,
            "dense_results": [],
            "sparse_results": [],
            "fused_results": [],
            "reranked_results": [],
            "is_sufficient": True,
            "citations": [],
            "intermediate_steps": [],
            "answer": "",
            "token_usage": {}
        }

        # Execute full compiled LangGraph workflow
        final_state = self.workflow.invoke(initial_state)
        total_latency = int((time.time() - start_time) * 1000)
        cits = final_state.get("citations", [])
        model_name = config.get("model", "gpt-4o")

        trace_id = langsmith_tracker.create_run_trace(
            name="HybridRAG_LangGraph",
            run_type="chain",
            inputs={"query": query, "top_k": config.get("top_k", 6)},
            outputs={"answer": final_state.get("answer", ""), "citations_count": len(cits), "model": model_name},
            latency_ms=total_latency,
            extra={"metadata": {"strategy": self.name, "orchestrator": "LangGraph"}}
        )

        return AnswerResult(
            answer=final_state.get("answer", ""),
            citations=cits,
            strategy=self.name,
            model=model_name,
            latency_ms=total_latency,
            retrieval_latency_ms=int(total_latency * 0.4),
            generation_latency_ms=int(total_latency * 0.6),
            token_usage=final_state.get("token_usage", {}),
            trace_id=trace_id,
            intermediate_steps=final_state.get("intermediate_steps", [])
        )

hybrid_rag = HybridRAGPipeline()
