import time
import json
import re
from typing import Dict, Any, List, cast
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
from apps.api.core.config import settings
from apps.api.schemas.rag import RetrievalResult, AnswerResult, Citation
from apps.api.rag.hybrid_rag import hybrid_rag
from apps.api.rag.hierarchical_rag import hierarchical_rag
from apps.api.rag.graph_rag import graph_rag
from apps.api.rag.agentic_rag import agentic_rag
from apps.api.rag.base import is_general_query, build_general_query_answer
from apps.api.core.langsmith import langsmith_tracker

class AdaptiveState(TypedDict):
    query: str
    corpus_id: str
    config: Dict[str, Any]
    difficulty: str
    target_strategy: str
    confidence: float
    reason: str
    classification_latency_ms: int
    citations: List[Citation]
    intermediate_steps: List[Dict[str, Any]]
    answer: str
    token_usage: Dict[str, int]
    delegated_result: Dict[str, Any]

class AdaptiveRAGPipeline:
    name = "Adaptive"

    def __init__(self):
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AdaptiveState)  # type: ignore

        workflow.add_node("classify_query_complexity", self._node_classify_query)
        workflow.add_node("compile_adaptive_telemetry", self._node_compile_telemetry)

        workflow.set_entry_point("classify_query_complexity")
        workflow.add_edge("classify_query_complexity", "compile_adaptive_telemetry")
        workflow.add_edge("compile_adaptive_telemetry", END)

        return workflow.compile()

    def classify_query(self, query: str) -> Dict[str, Any]:
        t0 = time.time()
        q_lower = query.lower()
        word_count = len(query.split())

        # Prompt-based structured classification when OpenAI is configured
        if settings.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=12.0)
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert research query classifier for an academic RAG system.\n"
                                "Classify the query into one of 4 routes:\n"
                                "1. 'simple': direct factual lookup, definition, author query, specific term lookup (routes to Hybrid RAG).\n"
                                "2. 'moderate': in-depth single paper methodology or mechanism explanation requiring deep section context (routes to Hierarchical RAG).\n"
                                "3. 'complex': multi-paper comparison, trade-offs, synthesis across papers, relational analysis (routes to GraphRAG).\n"
                                "4. 'agentic': ambiguous, multi-part, or exploratory query requiring self-reflective corrective retrieval (routes to Agentic RAG).\n"
                                "Respond in JSON format: {\"difficulty\": \"simple\"|\"moderate\"|\"complex\"|\"agentic\", \"confidence\": float (0.5-1.0), \"reason\": \"<1-sentence explanation>\"}"
                            )
                        },
                        {"role": "user", "content": query}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=120,
                    temperature=0.0
                )
                raw_content = resp.choices[0].message.content or "{}"
                parsed = json.loads(raw_content)
                diff = parsed.get("difficulty", "moderate").lower()
                conf = float(parsed.get("confidence", 0.90))
                reason = parsed.get("reason", "Query complexity analysis.")
                target = (
                    "Hybrid" if diff == "simple"
                    else "Hierarchical" if diff == "moderate"
                    else "GraphRAG" if diff == "complex"
                    else "Agentic"
                )
                latency = int((time.time() - t0) * 1000)
                return {
                    "difficulty": diff,
                    "target_strategy": target,
                    "confidence": conf,
                    "reason": reason,
                    "classification_latency_ms": latency
                }
            except Exception as e:
                print(f"[Adaptive Classification Notice] {e}")

        # Heuristic fallback classification
        latency = int((time.time() - t0) * 1000)
        if any(term in q_lower for term in ["compare", "versus", "vs", "relationship", "difference", "across", "trade-off"]):
            return {
                "difficulty": "complex",
                "target_strategy": "GraphRAG",
                "confidence": 0.92,
                "reason": "Comparative or relational multi-hop reasoning across papers detected.",
                "classification_latency_ms": latency
            }
        elif any(term in q_lower for term in ["verify", "correct", "evaluate", "synthesize all", "audit"]):
            return {
                "difficulty": "agentic",
                "target_strategy": "Agentic",
                "confidence": 0.88,
                "reason": "Self-reflective or corrective verification requirements detected.",
                "classification_latency_ms": latency
            }
        elif word_count > 12 or any(term in q_lower for term in ["why", "how", "mechanism", "limitation", "explain"]):
            return {
                "difficulty": "moderate",
                "target_strategy": "Hierarchical",
                "confidence": 0.85,
                "reason": "Detailed explanatory query requiring deep section context.",
                "classification_latency_ms": latency
            }
        else:
            return {
                "difficulty": "simple",
                "target_strategy": "Hybrid",
                "confidence": 0.95,
                "reason": "Direct factual or lookup query.",
                "classification_latency_ms": latency
            }

    def _node_classify_query(self, state: AdaptiveState) -> Dict[str, Any]:
        classification = self.classify_query(state["query"])
        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": "LangGraph: Dynamic Query Complexity Classification",
            "orchestrator": "LangGraph StateGraph Router",
            "difficulty": classification["difficulty"],
            "target_strategy": classification["target_strategy"],
            "confidence": classification["confidence"],
            "rationale": classification["reason"],
            "classification_latency_ms": classification["classification_latency_ms"]
        })
        return {
            "difficulty": classification["difficulty"],
            "target_strategy": classification["target_strategy"],
            "confidence": classification["confidence"],
            "reason": classification["reason"],
            "classification_latency_ms": classification["classification_latency_ms"],
            "intermediate_steps": steps
        }

    def _node_compile_telemetry(self, state: AdaptiveState) -> Dict[str, Any]:
        target = state.get("target_strategy", "Hybrid")
        conf = state.get("confidence", 0.90)
        steps = list(state.get("intermediate_steps", []))
        steps.append({
            "step": f"LangGraph: Delegated Pipeline Execution ({target})",
            "delegated_strategy": target,
            "routing_confidence": f"{int(conf * 100)}%",
            "status": "active"
        })
        return {"intermediate_steps": steps}

    def _get_target_pipeline(self, target_name: str):
        if target_name == "Hierarchical":
            return hierarchical_rag
        elif target_name == "GraphRAG":
            return graph_rag
        elif target_name == "Agentic":
            return agentic_rag
        return hybrid_rag

    async def retrieve(self, query: str, corpus_id: str, config: Dict[str, Any]) -> RetrievalResult:
        classification = self.classify_query(query)
        target = classification["target_strategy"]
        pipeline = self._get_target_pipeline(target)

        # Delegate retrieval to the selected pipeline
        sub_res = await pipeline.retrieve(query, corpus_id, config)

        steps = [
            {
                "step": "LangGraph: Dynamic Query Difficulty Classification",
                "difficulty": classification["difficulty"],
                "target_strategy": target,
                "confidence": classification["confidence"],
                "rationale": classification["reason"],
                "classification_latency_ms": classification["classification_latency_ms"]
            }
        ] + sub_res.intermediate_steps

        return RetrievalResult(
            query=query,
            strategy=self.name,
            citations=sub_res.citations,
            retrieval_latency_ms=sub_res.retrieval_latency_ms + classification["classification_latency_ms"],
            intermediate_steps=steps
        )

    async def generate(self, query: str, retrieval_result: RetrievalResult, config: Dict[str, Any]) -> AnswerResult:
        classification = self.classify_query(query)
        target = classification["target_strategy"]
        pipeline = self._get_target_pipeline(target)

        ans = await pipeline.generate(query, retrieval_result, config)
        ans.strategy = self.name
        if "#### " in ans.answer:
            adaptive_banner = (
                f"#### Adaptive Architecture Analysis (Dynamic Query Routing & Decomposition)\n"
                f"Query complexity classified as **{classification['difficulty'].upper()}** (confidence: {int(classification['confidence']*100)}%). "
                f"The adaptive dispatcher dynamically routed retrieval to the **{target} RAG** pipeline to maximize relational reasoning and evidence grounding across {len(ans.citations)} citations."
            )
            ans.answer = re.sub(r"#### [^\n]+Architecture Analysis[^\n]*\n[\s\S]*$", adaptive_banner, ans.answer)
        return ans

    async def run(self, query: str, corpus_id: str, config: Dict[str, Any]) -> AnswerResult:
        if is_general_query(query):
            return build_general_query_answer(query, self.name)

        start_time = time.time()
        initial_state: AdaptiveState = {
            "query": query,
            "corpus_id": corpus_id,
            "config": config,
            "difficulty": "",
            "target_strategy": "",
            "confidence": 0.0,
            "reason": "",
            "classification_latency_ms": 0,
            "citations": [],
            "intermediate_steps": [],
            "answer": "",
            "token_usage": {},
            "delegated_result": {}
        }

        # 1. Run classifier state graph
        state = self.workflow.invoke(initial_state)
        target = state["target_strategy"]
        pipeline = self._get_target_pipeline(target)

        # 2. Delegate execution to target pipeline instance
        sub_ans = await pipeline.run(query, corpus_id, config)

        total_latency = int((time.time() - start_time) * 1000)
        cits = sub_ans.citations
        model_name = config.get("model", "gpt-4o")

        # Enrich citations with adaptive strategy metadata
        for c in cits:
            if c.strategy_metadata:
                c.strategy_metadata["adaptive_route"] = target
                c.strategy_metadata["route_confidence"] = state["confidence"]
                c.strategy_metadata["route_difficulty"] = state["difficulty"]

        all_steps = state.get("intermediate_steps", []) + sub_ans.intermediate_steps

        trace_id = langsmith_tracker.create_run_trace(
            name="AdaptiveRAG_LangGraph",
            run_type="chain",
            inputs={"query": query, "classified_route": target, "confidence": state["confidence"]},
            outputs={"answer": sub_ans.answer, "citations_count": len(cits), "model": model_name},
            latency_ms=total_latency,
            extra={"metadata": {"strategy": self.name, "delegated_strategy": target, "orchestrator": "LangGraph"}}
        )

        # Format Adaptive architecture footer
        adaptive_banner = (
            f"#### Adaptive Architecture Analysis (Dynamic Query Routing & Decomposition)\n"
            f"Query complexity classified as **{state['difficulty'].upper()}** (confidence: {int(state['confidence']*100)}%). "
            f"The adaptive dispatcher dynamically routed retrieval to the **{target} RAG** pipeline to maximize relational reasoning and evidence grounding across {len(cits)} citations."
        )
        ans_text = sub_ans.answer
        if "#### " in ans_text:
            ans_text = re.sub(r"#### [^\n]+Architecture Analysis[^\n]*\n[\s\S]*$", adaptive_banner, ans_text)
        else:
            ans_text += f"\n\n---\n{adaptive_banner}"

        return AnswerResult(
            answer=ans_text,
            citations=cits,
            strategy=self.name,
            model=model_name,
            latency_ms=total_latency,
            retrieval_latency_ms=sub_ans.retrieval_latency_ms + state["classification_latency_ms"],
            generation_latency_ms=sub_ans.generation_latency_ms,
            token_usage=sub_ans.token_usage,
            trace_id=trace_id,
            intermediate_steps=all_steps
        )

adaptive_rag = AdaptiveRAGPipeline()
