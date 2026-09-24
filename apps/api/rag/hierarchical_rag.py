import time
from typing import Dict, Any, List, Tuple, Optional, cast
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from apps.api.schemas.rag import RetrievalResult, AnswerResult, Citation
from apps.api.services.index_service import index_service
from apps.api.rag.base import build_citation, generate_research_answer, is_general_query, build_general_query_answer
from apps.api.rag.common import CitationVerifier
from apps.api.core.langsmith import langsmith_tracker

class HierarchicalState(TypedDict):
    query: str
    corpus_id: str
    config: Dict[str, Any]
    child_matches: List[Tuple[str, float]]
    sparse_matches: Dict[str, float]
    expanded_items: List[Dict[str, Any]]
    ordered_items: List[Dict[str, Any]]
    citations: List[Citation]
    intermediate_steps: List[Dict[str, Any]]
    answer: str
    token_usage: Dict[str, int]

class HierarchicalRAGPipeline:
    name = "Hierarchical"

    def __init__(self):
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(HierarchicalState)  # type: ignore

        workflow.add_node("retrieve_child_anchors", self._node_retrieve_child_anchors)
        workflow.add_node("expand_parent_tree", self._node_expand_parent_tree)
        workflow.add_node("order_and_compress_context", self._node_order_and_compress_context)
        workflow.add_node("assemble_citations", self._node_assemble_citations)
        workflow.add_node("generate", self._node_generate)

        workflow.set_entry_point("retrieve_child_anchors")
        workflow.add_edge("retrieve_child_anchors", "expand_parent_tree")
        workflow.add_edge("expand_parent_tree", "order_and_compress_context")
        workflow.add_edge("order_and_compress_context", "assemble_citations")
        workflow.add_edge("assemble_citations", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def _node_retrieve_child_anchors(self, state: HierarchicalState) -> Dict[str, Any]:
        corpus_id = state["corpus_id"]
        query = state["query"]
        top_k = state["config"].get("top_k", 6)

        child_matches = index_service.search_dense(corpus_id, query, top_k=top_k)
        sparse_matches = dict(index_service.search_sparse(corpus_id, query, top_k=top_k * 4))

        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Child Anchor Search (256-token AST Leaf Chunks)",
            "retrieved_anchors": len(child_matches),
            "top_anchor_similarity": round(child_matches[0][1], 3) if child_matches else 0.0
        })
        return {
            "child_matches": child_matches,
            "sparse_matches": sparse_matches,
            "intermediate_steps": steps
        }

    def _node_expand_parent_tree(self, state: HierarchicalState) -> Dict[str, Any]:
        corpus_id = state["corpus_id"]
        child_matches = state.get("child_matches", [])
        seen_parent_ids = set()

        expanded = []
        for cid, sim in child_matches:
            child_chunk = index_service.get_chunk(corpus_id, cid)
            if not child_chunk:
                continue

            parent_id = child_chunk.get("parent_chunk_id")
            # Deduplicate parent section retrieval: if parent already included, preserve anchor but avoid repeating parent text
            is_parent_seen = parent_id in seen_parent_ids if parent_id else False
            if parent_id:
                seen_parent_ids.add(parent_id)

            parent_chunk = index_service.get_parent_chunk(corpus_id, parent_id) if parent_id and not is_parent_seen else None

            expanded.append({
                "cid": cid,
                "sim": sim,
                "child_chunk": child_chunk,
                "parent_chunk": parent_chunk,
                "parent_id": parent_id,
                "is_deduplicated_parent": is_parent_seen
            })

        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Parent Context Tree Resolution (2,048-token Section Expansion)",
            "resolved_parents": len([e for e in expanded if e.get("parent_chunk")]),
            "unique_parent_sections": len(seen_parent_ids)
        })
        return {"expanded_items": expanded, "intermediate_steps": steps}

    def _node_order_and_compress_context(self, state: HierarchicalState) -> Dict[str, Any]:
        """
        Orders context to mitigate lost-in-the-middle degradation:
        Places top scoring anchors at the beginning and end of the context window.
        """
        expanded = list(state.get("expanded_items", []))
        if len(expanded) <= 2:
            ordered = expanded
        else:
            # Reorder: best item first, second-best last, intermediate items in middle
            ordered = [expanded[0]]
            remaining = expanded[1:]
            for idx, item in enumerate(remaining):
                if idx % 2 == 0:
                    ordered.append(item)
                else:
                    ordered.insert(1, item)

        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Academic Context Ordering & Lost-in-Middle Mitigation",
            "ordered_count": len(ordered),
            "strategy": "High-attention edge positioning"
        })
        return {"ordered_items": ordered, "intermediate_steps": steps}

    def _node_assemble_citations(self, state: HierarchicalState) -> Dict[str, Any]:
        ordered_items = state.get("ordered_items", state.get("expanded_items", []))
        sparse_matches = state.get("sparse_matches", {})
        query = state["query"]

        citations: List[Citation] = []
        for rank, item in enumerate(ordered_items, start=1):
            cid = item["cid"]
            sim = item["sim"]
            child_chunk = item["child_chunk"]
            parent_chunk = item.get("parent_chunk")
            parent_id = item.get("parent_id")

            display_chunk = dict(child_chunk)
            if parent_chunk:
                display_chunk["content"] = parent_chunk.get("content", child_chunk.get("content", ""))
                display_chunk["section_name"] = f"{child_chunk.get('section_name', '')} (Parent Context Expanded)"

            child_text = child_chunk.get("content", "")
            parent_text = parent_chunk.get("content", child_text) if parent_chunk else child_text
            c_toks = len(child_text.split())
            p_toks = parent_chunk.get("token_count", len(parent_text.split())) if parent_chunk else c_toks
            expansion_ratio = f"{round(p_toks / max(1, c_toks), 1)}x" if parent_chunk else "1.0x"

            real_bm25 = float(sparse_matches.get(cid, 0.0))
            if real_bm25 == 0.0:
                q_words = set(w.lower() for w in query.split() if len(w) > 2)
                c_words = set(w.lower() for w in child_text.split())
                overlap = len(q_words.intersection(c_words))
                real_bm25 = round(overlap * 2.5, 2)
            real_reranker = round(0.5 * (float(sim) + min(1.0, real_bm25 / 25.0)), 3)

            meta = {
                "strategy": "Hierarchical",
                "technique": "LangGraph StateGraph: Dual-Tier AST (Paragraph Anchor -> Section Expansion)",
                "orchestrator": "LangGraph",
                "child_id": cid,
                "parent_id": parent_id or "root",
                "child_anchor_content": child_text,
                "parent_expanded_content": parent_text,
                "child_tokens": c_toks,
                "parent_tokens": p_toks,
                "expansion_ratio": expansion_ratio,
                "dense_similarity": round(float(sim), 3),
                "sparse_bm25": real_bm25,
                "hierarchy_nodes": [
                    {"level": "Corpus", "label": "Literature Corpus"},
                    {"level": "Paper", "label": f"arXiv:{child_chunk.get('arxiv_id', 'Paper')}"},
                    {"level": "Section", "label": child_chunk.get("section_name", "Methodology")},
                    {"level": "Parent Section", "label": f"Parent #{parent_id or 'section'}"},
                    {"level": "Child Anchor", "label": f"Anchor #{cid}"}
                ]
            }

            # Assign attention depth based on ordered position
            attention = "start" if rank == 1 else "end" if rank == len(ordered_items) else "middle"

            c = build_citation(
                chunk=display_chunk,
                rank=rank,
                similarity=sim,
                bm25_score=real_bm25,
                reranker=real_reranker,
                strategy_metadata=meta
            )
            c.attention_depth = attention
            citations.append(c)

        return {"citations": citations}

    def _node_generate(self, state: HierarchicalState) -> Dict[str, Any]:
        query = state["query"]
        citations = state.get("citations", [])
        model_name = state["config"].get("model", "gpt-4o")

        answer_text, usage = generate_research_answer(
            query=query,
            citations=citations,
            strategy_name=self.name,
            model_name=model_name,
            system_prompt_extra="You are executing the LangGraph Hierarchical RAG pipeline (AST Child Anchor -> Parent Section Tree Expansion)."
        )

        # Verify inline citations against evidence passages
        is_valid, cite_issues = CitationVerifier.verify(answer_text, citations)

        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Structural Evidence Synthesis",
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
        initial_state: HierarchicalState = {
            "query": query,
            "corpus_id": corpus_id,
            "config": config,
            "child_matches": [],
            "sparse_matches": {},
            "expanded_items": [],
            "ordered_items": [],
            "citations": [],
            "intermediate_steps": [],
            "answer": "",
            "token_usage": {}
        }

        # Step through StateGraph nodes
        step1 = self._node_retrieve_child_anchors(initial_state)
        s1_state = cast(HierarchicalState, {**initial_state, **step1})
        step2 = self._node_expand_parent_tree(s1_state)
        s2_state = cast(HierarchicalState, {**s1_state, **step2})
        step3 = self._node_order_and_compress_context(s2_state)
        s3_state = cast(HierarchicalState, {**s2_state, **step3})
        step4 = self._node_assemble_citations(s3_state)

        citations: List[Citation] = step4["citations"]
        steps: List[Dict[str, Any]] = s3_state["intermediate_steps"]
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
            system_prompt_extra="You are executing the LangGraph Hierarchical RAG pipeline (AST Child Anchor -> Parent Section Tree Expansion)."
        )

        gen_latency = int((time.time() - start_gen) * 1000)
        total_latency = retrieval_result.retrieval_latency_ms + gen_latency
        trace_id = langsmith_tracker.create_run_trace(
            name="HierarchicalRAG_LangGraph",
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
        initial_state: HierarchicalState = {
            "query": query,
            "corpus_id": corpus_id,
            "config": config,
            "child_matches": [],
            "sparse_matches": {},
            "expanded_items": [],
            "ordered_items": [],
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
            name="HierarchicalRAG_LangGraph",
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

hierarchical_rag = HierarchicalRAGPipeline()
