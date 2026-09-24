import os
import re
import numpy as np
import bm25s
import networkx as nx
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from openai import OpenAI
from apps.api.core.config import settings
from apps.api.services.neo4j_service import neo4j_service
from apps.api.services.graph_indexer import GraphIndexer

class IndexService:
    def __init__(self):
        self.sparse_indices: Dict[str, Any] = {}
        self.chunk_stores: Dict[str, Dict[str, Any]] = {}
        self.graphs: Dict[str, Any] = {}
        self.dense_vectors: Dict[str, Dict[str, np.ndarray]] = {}
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=4.0) if settings.OPENAI_API_KEY else None

    def index_corpus(self, corpus_id: str, chunks_data: List[Dict[str, Any]], sync_neo4j: bool = True):
        if not chunks_data:
            return

        corpus_chunk_store = {}
        child_corpus_texts = []
        child_corpus_ids = []

        for chunk in chunks_data:
            c_id = chunk["id"]
            corpus_chunk_store[c_id] = chunk

            if chunk.get("chunk_type") == "child":
                child_corpus_texts.append(chunk["content"])
                child_corpus_ids.append(c_id)

        # 1. Build and Persist NetworkX Knowledge Graph using GraphIndexer
        g = GraphIndexer.build_graph(chunks_data)
        self.chunk_stores[corpus_id] = corpus_chunk_store
        self.graphs[corpus_id] = g

        try:
            GraphIndexer.save_graph(g, corpus_id, settings.INDEX_DIR)
        except Exception as e:
            print(f"[IndexService] Graph persistence error: {e}")

        # 1. Build BM25s sparse index
        if child_corpus_texts:
            try:
                corpus_tokens = bm25s.tokenize(child_corpus_texts, stopwords="en")
                retriever = bm25s.BM25(corpus=child_corpus_ids)
                retriever.index(corpus_tokens)
                self.sparse_indices[corpus_id] = retriever
            except Exception as e:
                print(f"[IndexService] BM25s indexing error: {e}")

            # 2. Build or Load Cached Dense Embeddings
            self._build_or_load_dense_vectors(corpus_id, child_corpus_ids, child_corpus_texts)

        # 3. Synchronize to Neo4j Knowledge Graph (if available and requested)
        if sync_neo4j:
            try:
                if neo4j_service.is_available():
                    neo4j_service.sync_corpus_graph(corpus_id, chunks_data)
            except Exception as e:
                print(f"[IndexService] Neo4j sync notice: {e}")

    def _extract_graph_nodes(self, g: nx.Graph, chunk: Dict[str, Any]):
        content = chunk["content"]
        arxiv_id = chunk.get("arxiv_id", "")
        c_id = chunk["id"]

        method_patterns = [
            r"\b(Transformer|BERT|GPT|Attention Mechanism|Multi-Head Attention|FlashAttention|LoRA|QLoRA|BM25|BM25s|DPR|HNSW|RRF|Reciprocal Rank Fusion|CRAG|Self-RAG|FLARE|GraphRAG|Hierarchical RAG|Adaptive RAG|AST Chunking)\b"
        ]
        dataset_patterns = [
            r"\b(MS MARCO|Natural Questions|NQ|HotpotQA|TriviaQA|SQuAD|MMLU|GSM8K|HumanEval|GLUE|SuperGLUE|TREC|BEIR|ArXiv|PubMed|ImageNet|WikiText)\b"
        ]
        metric_patterns = [
            r"\b(BLEU|ROUGE|ROUGE-L|F1|Accuracy|Recall@\d+|Precision@\d+|MRR|nDCG|nDCG@\d+|Perplexity|Latency|Throughput)\b"
        ]
        concept_patterns = [
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b",
            r"\b(Superconductivity|Entanglement|Hamiltonian|Qubit|Surface Code|CRISPR|Cas9|Genome|Polymerase|RNA|Enzyme|Protein Folding|AlphaFold|Theorem|Conjecture|Manifold|Eigenvalue|Markov Chain|Bayesian|Stochastic)\b"
        ]

        stopwords = {"this", "that", "these", "those", "from", "with", "have", "been", "figure", "table", "section", "paper"}

        # Extract Methods
        for pat in method_patterns:
            for m in re.findall(pat, content, re.IGNORECASE):
                term = m.strip()
                if not g.has_node(term):
                    g.add_node(term, type="method", chunk_ids=[])
                g.nodes[term]["chunk_ids"].append(c_id)

        # Extract Datasets
        for pat in dataset_patterns:
            for d in re.findall(pat, content, re.IGNORECASE):
                term = d.strip()
                if not g.has_node(term):
                    g.add_node(term, type="dataset", chunk_ids=[])
                g.nodes[term]["chunk_ids"].append(c_id)

        # Extract Metrics
        for pat in metric_patterns:
            for met in re.findall(pat, content, re.IGNORECASE):
                term = met.strip()
                if not g.has_node(term):
                    g.add_node(term, type="metric", chunk_ids=[])
                g.nodes[term]["chunk_ids"].append(c_id)

        # Extract Concepts
        found_entities = set()
        for pat in concept_patterns:
            for m in re.findall(pat, content, re.IGNORECASE):
                if isinstance(m, tuple):
                    m = m[0]
                term = m.strip().title()
                if len(term) > 3 and term.lower() not in stopwords:
                    found_entities.add(term)

        for ent in found_entities:
            if not g.has_node(ent):
                g.add_node(ent, type="concept", chunk_ids=[])
            g.nodes[ent]["chunk_ids"].append(c_id)

        all_nodes = list(found_entities)[:8]
        for i in range(len(all_nodes)):
            for j in range(i + 1, len(all_nodes)):
                e1, e2 = all_nodes[i], all_nodes[j]
                if g.has_edge(e1, e2):
                    g[e1][e2]["weight"] += 1
                else:
                    g.add_edge(e1, e2, weight=1, paper=arxiv_id)

    def get_community_clusters(self, corpus_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        self._ensure_corpus_loaded(corpus_id)
        # Check Neo4j first
        try:
            if neo4j_service.is_available():
                clusters = neo4j_service.get_community_clusters(corpus_id, limit=limit)
                if clusters:
                    return clusters
        except Exception:
            pass

        # Fallback to NetworkX greedy modularity communities
        g = self.graphs.get(corpus_id)
        if not g or len(g) < 2:
            return []

        try:
            import networkx.algorithms.community as nx_comm
            communities = list(nx_comm.greedy_modularity_communities(g))
            results = []
            for idx, comm in enumerate(communities[:limit]):
                nodes_sorted = sorted(list(comm), key=lambda n: g.degree(n), reverse=True)
                if nodes_sorted:
                    top_node = nodes_sorted[0]
                    related = [str(n) for n in nodes_sorted[1:4]]
                    results.append({
                        "theme": str(top_node),
                        "papers": related,
                        "datasets": [str(n) for n in nodes_sorted if g.nodes[n].get("type") == "dataset"][:2],
                        "centrality": g.degree(top_node)
                    })
            return results
        except Exception as e:
            print(f"[IndexService] Community detection notice: {e}")
            return []

    def _build_or_load_dense_vectors(self, corpus_id: str, chunk_ids: List[str], texts: List[str]):
        cache_file = settings.INDEX_DIR / f"{corpus_id}_dense.npz"

        # Check disk cache first for instant millisecond load
        if cache_file.exists():
            try:
                npz = np.load(str(cache_file))
                loaded = {k: npz[k] for k in npz.files}
                if all(cid in loaded for cid in chunk_ids):
                    self.dense_vectors[corpus_id] = loaded
                    return
            except Exception as e:
                print(f"[IndexService] Cache load notice: {e}")

        corpus_vecs = {}
        if self.openai_client and texts:
            try:
                batch_size = 64
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i : i + batch_size]
                    batch_ids = chunk_ids[i : i + batch_size]

                    clean_texts = [t.replace("\n", " ")[:4000] for t in batch_texts]
                    res = self.openai_client.embeddings.create(
                        input=clean_texts,
                        model=settings.DEFAULT_EMBEDDING_MODEL
                    )
                    for cid, emb_item in zip(batch_ids, res.data):
                        vec = np.array(emb_item.embedding, dtype=np.float32)
                        norm = np.linalg.norm(vec)
                        corpus_vecs[cid] = vec / (norm + 1e-9)

                self.dense_vectors[corpus_id] = corpus_vecs
                try:
                    np.savez_compressed(str(cache_file), **corpus_vecs)
                except Exception:
                    pass
                return
            except Exception as e:
                if "429" in str(e) or "quota" in str(e) or "credit" in str(e):
                    self.openai_client = None
                print(f"[IndexService] OpenAI embedding error: {e}. Falling back to deterministic vectors.")

        for c_id, text in zip(chunk_ids, texts):
            np.random.seed(abs(hash(c_id)) % (2**32))
            v = np.random.randn(1536).astype(np.float32)
            norm = np.linalg.norm(v)
            corpus_vecs[c_id] = v / (norm + 1e-9)

        self.dense_vectors[corpus_id] = corpus_vecs

    def _ensure_corpus_loaded(self, corpus_id: str):
        # 1. Check if graph can be loaded from disk cache if not in memory
        if corpus_id not in self.graphs:
            disk_g = GraphIndexer.load_graph(corpus_id, settings.INDEX_DIR)
            if disk_g is not None:
                self.graphs[corpus_id] = disk_g

        if corpus_id in self.chunk_stores and len(self.chunk_stores[corpus_id]) > 0:
            return

        db_file = settings.DATA_DIR / "arxiv_rag.db"
        if not db_file.exists():
            return

        import sqlite3
        try:
            conn = sqlite3.connect(str(db_file))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT c.id, c.corpus_id, c.paper_id, c.arxiv_id, c.page_number, c.section_name,
                       c.chunk_type, c.parent_chunk_id, c.content, c.token_count, p.title as paper_title
                FROM chunks c
                LEFT JOIN papers p ON c.paper_id = p.id
                WHERE c.corpus_id = ?
            """, (corpus_id,))
            rows = cur.fetchall()
            conn.close()

            if rows:
                chunks_data = [dict(r) for r in rows]
                self.index_corpus(corpus_id, chunks_data, sync_neo4j=False)
        except Exception as e:
            print(f"[IndexService] Auto-load error for {corpus_id}: {e}")

    def get_query_vector(self, query: str) -> np.ndarray:
        q_vec = None
        if self.openai_client:
            try:
                res = self.openai_client.embeddings.create(
                    input=[query.replace("\n", " ")],
                    model=settings.DEFAULT_EMBEDDING_MODEL
                )
                q_vec = np.array(res.data[0].embedding, dtype=np.float32)
                q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-9)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e) or "credit" in str(e):
                    self.openai_client = None
                print(f"[IndexService] Query embedding error: {e}")

        if q_vec is None:
            np.random.seed(abs(hash(query)) % (2**32))
            q_vec = np.random.randn(1536).astype(np.float32)
            q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-9)
        return q_vec

    def get_chunk_similarity(self, corpus_id: str, chunk_id: str, query: str) -> float:
        self._ensure_corpus_loaded(corpus_id)
        vecs = self.dense_vectors.get(corpus_id, {})
        doc_vec = vecs.get(chunk_id)
        if doc_vec is None:
            return 0.72
        q_vec = self.get_query_vector(query)
        return round(float(np.dot(q_vec, doc_vec)), 3)

    def search_dense(self, corpus_id: str, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        self._ensure_corpus_loaded(corpus_id)
        vecs = self.dense_vectors.get(corpus_id)
        if not vecs:
            return []

        q_vec = self.get_query_vector(query)

        scores = []
        is_ref_query = any(k in query.lower() for k in ("reference", "bibliography", "citation", "author", "cite"))
        for cid, doc_vec in vecs.items():
            sim = float(np.dot(q_vec, doc_vec))
            chunk = self.chunk_stores.get(corpus_id, {}).get(cid, {})
            sec_name = (chunk.get("section_name") or "").lower()
            if not is_ref_query and any(k in sec_name for k in ("reference", "bibliography", "acknowledgement", "acknowledgments")):
                sim -= 0.30  # Demote reference list chunks
            scores.append((cid, float(sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def search_sparse(self, corpus_id: str, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        self._ensure_corpus_loaded(corpus_id)
        retriever = self.sparse_indices.get(corpus_id)
        if not retriever:
            return []

        try:
            query_tokens = bm25s.tokenize([query], stopwords="en")
            results, scores = retriever.retrieve(query_tokens, k=min(top_k * 2, len(retriever.corpus)))
            output = []
            is_ref_query = any(k in query.lower() for k in ("reference", "bibliography", "citation", "author", "cite"))
            if len(results) > 0:
                for cid, score in zip(results[0], scores[0]):
                    chunk = self.chunk_stores.get(corpus_id, {}).get(str(cid), {})
                    sec_name = (chunk.get("section_name") or "").lower()
                    penalized = float(score)
                    if not is_ref_query and any(k in sec_name for k in ("reference", "bibliography", "acknowledgement", "acknowledgments")):
                        penalized = max(0.0, penalized - 8.0)
                    output.append((str(cid), penalized))
                output.sort(key=lambda x: x[1], reverse=True)
            return output[:top_k]
        except Exception as e:
            print(f"[IndexService] BM25s retrieve error: {e}")
            return []

    def get_chunk(self, corpus_id: str, chunk_id: str) -> Dict[str, Any]:
        self._ensure_corpus_loaded(corpus_id)
        return self.chunk_stores.get(corpus_id, {}).get(chunk_id, {})

    def get_parent_chunk(self, corpus_id: str, parent_id: Optional[str]) -> Dict[str, Any]:
        if not parent_id:
            return {}
        self._ensure_corpus_loaded(corpus_id)
        return self.chunk_stores.get(corpus_id, {}).get(parent_id, {})

    def traverse_graph(self, corpus_id: str, query: str, top_k: int = 5, max_hops: int = 2) -> Dict[str, Any]:
        """Performs bounded 1-hop and 2-hop traversal with full telemetry and path representations."""
        self._ensure_corpus_loaded(corpus_id)
        g = self.graphs.get(corpus_id)
        if not g:
            return {
                "matched_nodes": [],
                "ranked_nodes": [],
                "traversed_edges": [],
                "paths": [],
                "retrieved_chunk_ids": [],
                "telemetry": {
                    "nodes_matched": 0,
                    "nodes_traversed": 0,
                    "number_of_hops": 0,
                    "edges_traversed": 0,
                    "subgraph_size": {"nodes": 0, "edges": 0},
                    "retrieved_chunks": 0
                }
            }

        return GraphIndexer.multi_hop_traversal(g, query, top_k_nodes=top_k, max_hops=max_hops)

    def search_graph(self, corpus_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        self._ensure_corpus_loaded(corpus_id)

        # 1. Try querying Neo4j knowledge graph first (only if it contains chunks for this corpus)
        try:
            if neo4j_service.is_available():
                neo_results = neo4j_service.search_graph(corpus_id, query, top_k=top_k)
                if neo_results and any(len(r.get("chunk_ids", [])) > 0 for r in neo_results):
                    return neo_results
        except Exception as e:
            print(f"[IndexService] Neo4j query notice: {e}")

        # 2. NetworkX Bounded Multi-Hop Traversal via GraphIndexer
        g = self.graphs.get(corpus_id)
        if not g:
            return []

        traversal = GraphIndexer.multi_hop_traversal(g, query, top_k_nodes=top_k, max_hops=2)
        ranked = traversal.get("ranked_nodes", [])
        paths = traversal.get("paths", [])
        telemetry = traversal.get("telemetry", {})

        results = []
        for r in ranked[:top_k]:
            ent = r["entity"]
            neighbors = list(g.successors(ent)) + list(g.predecessors(ent)) if hasattr(g, "successors") else list(g.neighbors(ent))
            results.append({
                "entity": ent,
                "type": r.get("type", "concept"),
                "neighbors": [str(n) for n in neighbors[:8]],
                "chunk_ids": r.get("chunk_ids", [])[:8],
                "degree": r.get("degree", g.degree(ent)),
                "path_score": r.get("score", 1.0),
                "hop": r.get("hop", 0),
                "paths": [p for p in paths if p["source"] == ent or p["target"] == ent],
                "telemetry": telemetry
            })

        return results

    def get_community_clusters(self, corpus_id: str, limit: int = 4) -> List[Dict[str, Any]]:
        self._ensure_corpus_loaded(corpus_id)

        # 1. Try Neo4j first
        try:
            if neo4j_service.is_available():
                clusters = neo4j_service.get_community_clusters(corpus_id, limit=limit)
                if clusters:
                    return clusters
        except Exception as e:
            print(f"[IndexService] Neo4j community notice: {e}")

        # 2. Fallback to NetworkX communities
        g = self.graphs.get(corpus_id)
        if not g or len(g.nodes()) == 0:
            return []

        clusters = []
        try:
            from networkx.algorithms import community
            # Convert to undirected graph for community detection if directed
            undir_g = g.to_undirected() if hasattr(g, "to_undirected") else g
            comms = list(community.greedy_modularity_communities(undir_g))
            for i, comm in enumerate(comms[:limit]):
                nodes_list = list(comm)[:6]
                chunks_set = set()
                for n in nodes_list:
                    chunks_set.update(g.nodes[n].get("chunk_ids", [])[:2])
                clusters.append({
                    "theme": f"Community #{i+1}: {', '.join(str(n) for n in nodes_list[:3])}",
                    "arxiv_id": "Subgraph Cluster",
                    "entities": [str(n) for n in nodes_list],
                    "chunk_ids": list(chunks_set)[:5]
                })
        except Exception:
            # Simple degree-based fallback
            top_nodes = sorted(g.nodes(), key=lambda n: g.degree(n), reverse=True)[:limit]
            for n in top_nodes:
                nbrs = list(g.successors(n)) if hasattr(g, "successors") else list(g.neighbors(n))
                c_ids = g.nodes[n].get("chunk_ids", [])[:4]
                clusters.append({
                    "theme": f"Cluster: {n}",
                    "arxiv_id": "NetworkX",
                    "entities": [str(n)] + [str(nb) for nb in nbrs[:5]],
                    "chunk_ids": c_ids
                })
        return clusters

    def remove_corpus(self, corpus_id: str):
        self.sparse_indices.pop(corpus_id, None)
        self.chunk_stores.pop(corpus_id, None)
        self.graphs.pop(corpus_id, None)
        self.dense_vectors.pop(corpus_id, None)

        # Remove serialized graph & cache files from disk
        for ext in ["_graph.json", "_graph.pkl", "_dense.npz"]:
            fpath = settings.INDEX_DIR / f"{corpus_id}{ext}"
            if fpath.exists():
                try:
                    fpath.unlink()
                except Exception as e:
                    print(f"[IndexService] Could not remove index file {fpath}: {e}")

index_service = IndexService()
