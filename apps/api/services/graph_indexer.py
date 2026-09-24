import re
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
import networkx as nx  # type: ignore

# -------------------------------------------------------------------------
# 1. Entity Normalizer: Canonical Names, Aliases, Case Normalization
# -------------------------------------------------------------------------

# Canonical mapping dictionary: maps lowercase aliases and acronyms to (Canonical Name, Entity Type)
CANONICAL_ENTITIES: Dict[str, Tuple[str, str]] = {
    # Models & Architectures
    "llm": ("Large Language Model", "model"),
    "large language model": ("Large Language Model", "model"),
    "large language models": ("Large Language Model", "model"),
    "transformer": ("Transformer", "model"),
    "transformers": ("Transformer", "model"),
    "bert": ("BERT", "model"),
    "gpt": ("GPT", "model"),
    "gpt-3": ("GPT-3", "model"),
    "gpt-4": ("GPT-4", "model"),
    "gpt-4o": ("GPT-4o", "model"),
    "llama": ("Llama", "model"),
    "llama-2": ("Llama-2", "model"),
    "llama-3": ("Llama-3", "model"),
    "mistral": ("Mistral", "model"),
    "cnn": ("Convolutional Neural Network", "model"),
    "convolutional neural network": ("Convolutional Neural Network", "model"),
    "convolutional neural networks": ("Convolutional Neural Network", "model"),
    "rnn": ("Recurrent Neural Network", "model"),
    "recurrent neural network": ("Recurrent Neural Network", "model"),
    "recurrent neural networks": ("Recurrent Neural Network", "model"),
    "lstm": ("Long Short-Term Memory", "model"),
    "vit": ("Vision Transformer", "model"),
    "vision transformer": ("Vision Transformer", "model"),
    "vision transformers": ("Vision Transformer", "model"),
    "resnet": ("ResNet", "model"),
    "u-net": ("U-Net", "model"),
    "unet": ("U-Net", "model"),
    "diffusion model": ("Diffusion Model", "model"),
    "diffusion models": ("Diffusion Model", "model"),
    "vae": ("Variational Autoencoder", "model"),
    "autoencoder": ("Autoencoder", "model"),
    "autoencoders": ("Autoencoder", "model"),
    "crag": ("Corrective RAG", "model"),
    "self-rag": ("Self-RAG", "model"),
    "flare": ("FLARE", "model"),

    # Methods & Mechanisms
    "rag": ("Retrieval-Augmented Generation", "method"),
    "retrieval augmented generation": ("Retrieval-Augmented Generation", "method"),
    "retrieval-augmented generation": ("Retrieval-Augmented Generation", "method"),
    "graphrag": ("GraphRAG", "method"),
    "graph rag": ("GraphRAG", "method"),
    "bm25": ("BM25", "method"),
    "bm-25": ("BM25", "method"),
    "bm25s": ("BM25s", "method"),
    "dense retrieval": ("Dense Retrieval", "method"),
    "sparse retrieval": ("Sparse Retrieval", "method"),
    "rrf": ("Reciprocal Rank Fusion", "method"),
    "reciprocal rank fusion": ("Reciprocal Rank Fusion", "method"),
    "hnsw": ("Hierarchical Navigable Small World", "method"),
    "dpr": ("Dense Passage Retrieval", "method"),
    "self-attention": ("Self-Attention", "method"),
    "self attention": ("Self-Attention", "method"),
    "multi-head attention": ("Multi-Head Attention", "method"),
    "multihead attention": ("Multi-Head Attention", "method"),
    "mha": ("Multi-Head Attention", "method"),
    "flashattention": ("FlashAttention", "method"),
    "flash attention": ("FlashAttention", "method"),
    "lora": ("LoRA", "method"),
    "qlora": ("QLoRA", "method"),
    "dpo": ("Direct Preference Optimization", "method"),
    "direct preference optimization": ("Direct Preference Optimization", "method"),
    "ppo": ("Proximal Policy Optimization", "method"),
    "rlhf": ("Reinforcement Learning from Human Feedback", "method"),
    "reinforcement learning": ("Reinforcement Learning", "method"),
    "contrastive learning": ("Contrastive Learning", "method"),
    "transfer learning": ("Transfer Learning", "method"),
    "beam search": ("Beam Search", "method"),
    "ast chunking": ("AST Chunking", "method"),
    "parent-child chunking": ("Parent-Child Chunking", "method"),
    "chain-of-thought": ("Chain-of-Thought", "method"),
    "cot": ("Chain-of-Thought", "method"),
    "tree-of-thought": ("Tree-of-Thought", "method"),

    # Datasets
    "ms marco": ("MS MARCO", "dataset"),
    "msmarco": ("MS MARCO", "dataset"),
    "natural questions": ("Natural Questions", "dataset"),
    "nq": ("Natural Questions", "dataset"),
    "hotpotqa": ("HotpotQA", "dataset"),
    "hotpot qa": ("HotpotQA", "dataset"),
    "triviaqa": ("TriviaQA", "dataset"),
    "squad": ("SQuAD", "dataset"),
    "squad 2.0": ("SQuAD", "dataset"),
    "mmlu": ("MMLU", "dataset"),
    "gsm8k": ("GSM8K", "dataset"),
    "humaneval": ("HumanEval", "dataset"),
    "glue": ("GLUE", "dataset"),
    "superglue": ("SuperGLUE", "dataset"),
    "trec": ("TREC", "dataset"),
    "beir": ("BEIR", "dataset"),
    "imagenet": ("ImageNet", "dataset"),
    "pubmed": ("PubMed", "dataset"),
    "wikitext": ("WikiText", "dataset"),

    # Metrics
    "bleu": ("BLEU", "metric"),
    "rouge": ("ROUGE", "metric"),
    "rouge-1": ("ROUGE-1", "metric"),
    "rouge-2": ("ROUGE-2", "metric"),
    "rouge-l": ("ROUGE-L", "metric"),
    "f1": ("F1 Score", "metric"),
    "f1 score": ("F1 Score", "metric"),
    "accuracy": ("Accuracy", "metric"),
    "precision": ("Precision", "metric"),
    "recall": ("Recall", "metric"),
    "mrr": ("MRR", "metric"),
    "mean reciprocal rank": ("MRR", "metric"),
    "ndcg": ("nDCG", "metric"),
    "ndcg@10": ("nDCG@10", "metric"),
    "perplexity": ("Perplexity", "metric"),
    "latency": ("Latency", "metric"),
    "throughput": ("Throughput", "metric"),
    "faithfulness": ("Faithfulness", "metric"),

    # Concepts & Principles
    "knowledge graph": ("Knowledge Graph", "concept"),
    "knowledge graphs": ("Knowledge Graph", "concept"),
    "kg": ("Knowledge Graph", "concept"),
    "multi-hop traversal": ("Multi-Hop Traversal", "concept"),
    "multihop traversal": ("Multi-Hop Traversal", "concept"),
    "multi-hop reasoning": ("Multi-Hop Reasoning", "concept"),
    "community detection": ("Community Detection", "concept"),
    "modularity": ("Modularity", "concept"),
    "centrality": ("Centrality", "concept"),
    "subgraph": ("Subgraph", "concept"),
    "semantic search": ("Semantic Search", "concept"),
    "vector embeddings": ("Vector Embeddings", "concept"),
    "quantization": ("Quantization", "concept"),
    "overfitting": ("Overfitting", "concept"),
    "generalization": ("Generalization", "concept"),
    "inductive bias": ("Inductive Bias", "concept"),
    "cancer detection": ("Cancer Detection", "concept"),
    "early detection": ("Early Detection", "concept"),
    "biomarker discovery": ("Biomarker Discovery", "concept"),
    "histopathology": ("Histopathology", "concept"),
    "genomics": ("Genomics", "concept"),

    # Technologies & Frameworks
    "pytorch": ("PyTorch", "technology"),
    "tensorflow": ("TensorFlow", "technology"),
    "networkx": ("NetworkX", "technology"),
    "neo4j": ("Neo4j", "technology"),
    "langgraph": ("LangGraph", "technology"),
    "langsmith": ("LangSmith", "technology"),
    "vllm": ("vLLM", "technology"),
    "huggingface": ("HuggingFace", "technology"),
    "cuda": ("CUDA", "technology"),
    "pymupdf": ("PyMuPDF", "technology"),
    "fitz": ("PyMuPDF", "technology"),
}

class EntityNormalizer:
    """Normalizes raw terms, expands acronyms, resolves aliases, and prevents duplicate nodes."""

    STOPWORDS: Set[str] = {
        "the", "a", "an", "is", "are", "was", "were", "and", "or", "for", "to", "in", "on", "of",
        "this", "that", "these", "those", "from", "with", "have", "been", "had", "has",
        "figure", "table", "section", "paper", "author", "authors", "result", "results",
        "method", "methods", "model", "models", "approach", "approaches", "study", "work",
        "state", "level", "use", "uses", "used", "using", "based", "first", "second", "third",
        "how", "what", "which", "why", "where", "who", "whom", "whose", "can", "could",
        "would", "should", "does", "do", "did", "et", "al"
    }

    @classmethod
    def normalize(cls, term: str) -> Optional[Tuple[str, str]]:
        """
        Takes a raw entity string and returns (canonical_name, entity_type),
        or None if the term is invalid/stopword.
        """
        if not term:
            return None
        clean = term.strip().strip("'\"()[]{}.,;:").strip()
        if len(clean) < 2:
            return None

        lower = clean.lower()
        if lower.startswith("the "):
            clean = clean[4:].strip()
            lower = clean.lower()
        elif lower.startswith("a "):
            clean = clean[2:].strip()
            lower = clean.lower()
        elif lower.startswith("an "):
            clean = clean[3:].strip()
            lower = clean.lower()

        if len(clean) < 2 or lower in cls.STOPWORDS:
            return None

        # 1. Direct dictionary match
        if lower in CANONICAL_ENTITIES:
            return CANONICAL_ENTITIES[lower]

        # 2. Plural strip match (e.g. 'transformers' -> 'transformer')
        if lower.endswith("s") and lower[:-1] in CANONICAL_ENTITIES:
            return CANONICAL_ENTITIES[lower[:-1]]

        # 3. Clean casing: maintain all-caps for short acronyms (e.g., CNN, RAG, BERT), title casing otherwise
        if len(clean) <= 5 and clean.isupper():
            canonical = clean
        else:
            canonical = clean.title()

        return canonical, "concept"

    @classmethod
    def get_aliases(cls, canonical_name: str) -> List[str]:
        """Returns all recognized aliases for a given canonical name."""
        aliases = []
        for alias, (cname, _) in CANONICAL_ENTITIES.items():
            if cname.lower() == canonical_name.lower() and alias != canonical_name.lower():
                aliases.append(alias)
        return aliases


# -------------------------------------------------------------------------
# 2. Entity & Concept Extractor
# -------------------------------------------------------------------------

class EntityExtractor:
    """Extracts typed entities from scientific text chunks across 7 categories."""

    # Explicit regex patterns for specific high-signal entities
    PATTERNS: List[Tuple[str, str]] = [
        # Models
        (r"\b(Transformer|BERT|GPT|GPT-3|GPT-4|GPT-4o|Llama|Llama-2|Llama-3|Mistral|ResNet|U-Net|Vision Transformer|ViT|CNN|RNN|LSTM|Diffusion Model|Autoencoder|VAE|CRAG|Self-RAG|FLARE)\b", "model"),
        # Methods
        (r"\b(Retrieval-Augmented Generation|RAG|GraphRAG|BM25|BM25s|Dense Retrieval|Sparse Retrieval|Reciprocal Rank Fusion|RRF|HNSW|DPR|Self-Attention|Multi-Head Attention|FlashAttention|LoRA|QLoRA|Direct Preference Optimization|DPO|PPO|Reinforcement Learning|RLHF|Contrastive Learning|Transfer Learning|AST Chunking|Parent-Child Chunking|Chain-of-Thought|CoT)\b", "method"),
        # Datasets
        (r"\b(MS MARCO|Natural Questions|HotpotQA|TriviaQA|SQuAD|MMLU|GSM8K|HumanEval|GLUE|SuperGLUE|TREC|BEIR|ImageNet|PubMed|WikiText)\b", "dataset"),
        # Metrics
        (r"\b(BLEU|ROUGE|ROUGE-L|F1|Accuracy|Recall@\d+|Precision@\d+|MRR|nDCG|nDCG@\d+|Perplexity|Latency|Throughput|Faithfulness)\b", "metric"),
        # Technologies
        (r"\b(PyTorch|TensorFlow|NetworkX|Neo4j|LangGraph|LangSmith|vLLM|HuggingFace|CUDA|PyMuPDF)\b", "technology"),
        # Concepts
        (r"\b(Knowledge Graph|Multi-Hop Traversal|Multi-Hop Reasoning|Community Detection|Modularity|Centrality|Subgraph|Semantic Search|Vector Embeddings|Quantization|Overfitting|Generalization|Inductive Bias|Cancer Detection|Early Detection|Biomarker Discovery|Histopathology|Genomics)\b", "concept"),
    ]

    # Academic capitalized phrases (2-3 words) e.g. "Convolutional Neural Network", "Reciprocal Rank Fusion"
    COMPOUND_PHRASE_RE = re.compile(r"\b[A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+){1,2}\b")

    @classmethod
    def extract_entities(cls, text: str) -> List[Dict[str, Any]]:
        """
        Extracts all recognized and normalized entities from a chunk of text.
        Returns a list of dicts: [{'canonical_name': ..., 'entity_type': ..., 'raw': ...}]
        """
        found: Dict[str, Dict[str, Any]] = {}

        # 1. Pattern-based typed extraction
        for pat, default_type in cls.PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                raw = m.group(0).strip()
                norm = EntityNormalizer.normalize(raw)
                if norm:
                    cname, etype = norm
                    # prefer specific type over generic 'concept'
                    if etype == "concept" and default_type != "concept":
                        etype = default_type
                    if cname not in found:
                        found[cname] = {
                            "canonical_name": cname,
                            "entity_type": etype,
                            "raw": raw,
                            "span": (m.start(), m.end())
                        }

        # 2. Academic noun phrases (e.g., "Cancer Detection", "Transfer Learning")
        for m in cls.COMPOUND_PHRASE_RE.finditer(text):
            raw = m.group(0).strip()
            norm = EntityNormalizer.normalize(raw)
            if norm:
                cname, etype = norm
                if cname not in found:
                    found[cname] = {
                        "canonical_name": cname,
                        "entity_type": etype,
                        "raw": raw,
                        "span": (m.start(), m.end())
                    }

        return list(found.values())


# -------------------------------------------------------------------------
# 3. Relationship Extractor: Semantic Directed Edges + Co-occurrence Fallback
# -------------------------------------------------------------------------

class RelationExtractor:
    """
    Extracts directed semantic relationships between entities occurring within a chunk:
    - uses / utilizes
    - evaluates_on / benchmarks_on
    - outperforms / exceeds
    - optimizes / improves
    - combined_with / integrated_with
    - proposes / introduces
    - applies_to / applied_to
    Plus proximity-based co-occurrence fallback.
    """

    RELATION_PATTERNS = [
        ("uses", re.compile(r"\b(uses|utilizes|utilize|employ|employs|relying on|relies on|is based on|incorporates|leverages|leveraging|incorporating)\b", re.IGNORECASE)),
        ("evaluates_on", re.compile(r"\b(evaluated on|evaluates on|tested on|benchmarked on|benchmarked against|trained on|experiments on)\b", re.IGNORECASE)),
        ("outperforms", re.compile(r"\b(outperforms|exceeds|surpasses|beats|achieves higher \w+ than)\b", re.IGNORECASE)),
        ("optimizes", re.compile(r"\b(optimizes|improves|enhances|accelerates|boosts|fine-tunes|tunes|adapts)\b", re.IGNORECASE)),
        ("combined_with", re.compile(r"\b(combined with|fused with|integrated with|jointly with|coupled with|hybridized with)\b", re.IGNORECASE)),
        ("proposes", re.compile(r"\b(proposes|introduces|presents|develops|designs)\b", re.IGNORECASE)),
        ("applies_to", re.compile(r"\b(applies to|applied to|implemented for|adapted for)\b", re.IGNORECASE)),
    ]

    @classmethod
    def extract_relations(
        cls,
        text: str,
        entities: List[Dict[str, Any]],
        chunk_id: str,
        paper_id: str,
        arxiv_id: str,
        section_name: str,
        page_number: int
    ) -> List[Dict[str, Any]]:
        """
        Finds directed relations between entities in the text chunk.
        """
        relations = []
        if len(entities) < 2:
            return relations

        # Map entities by sentence for locality
        sentences = re.split(r"(?<=[.!?])\s+", text)
        linked_pairs: Set[Tuple[str, str]] = set()

        for s in sentences:
            s_ents = [e for e in entities if e["canonical_name"].lower() in s.lower() or e["raw"].lower() in s.lower()]
            if len(s_ents) < 2:
                continue

            for i in range(len(s_ents)):
                for j in range(len(s_ents)):
                    if i == j:
                        continue
                    src = s_ents[i]["canonical_name"]
                    tgt = s_ents[j]["canonical_name"]
                    if src == tgt or (src, tgt) in linked_pairs:
                        continue

                    # Search text between src and tgt in sentence
                    src_pos = s.lower().find(s_ents[i]["raw"].lower())
                    tgt_pos = s.lower().find(s_ents[j]["raw"].lower())

                    if src_pos != -1 and tgt_pos != -1 and src_pos < tgt_pos:
                        between_text = s[src_pos + len(s_ents[i]["raw"]):tgt_pos]
                        matched_rel = None
                        for rel_name, rel_re in cls.RELATION_PATTERNS:
                            if rel_re.search(between_text):
                                matched_rel = rel_name
                                break

                        if matched_rel:
                            linked_pairs.add((src, tgt))
                            relations.append({
                                "source": src,
                                "target": tgt,
                                "relation": matched_rel,
                                "weight": 1.0,
                                "confidence": 0.88,
                                "chunk_id": chunk_id,
                                "paper_id": paper_id,
                                "arxiv_id": arxiv_id,
                                "section_name": section_name,
                                "page_number": page_number,
                                "evidence_text": s.strip()[:200]
                            })

        # Co-occurrence fallback for entities in the same chunk without a discovered semantic edge
        ent_names = [e["canonical_name"] for e in entities]
        for i in range(len(ent_names)):
            for j in range(i + 1, min(i + 4, len(ent_names))):
                src, tgt = ent_names[i], ent_names[j]
                if (src, tgt) not in linked_pairs and (tgt, src) not in linked_pairs:
                    linked_pairs.add((src, tgt))
                    relations.append({
                        "source": src,
                        "target": tgt,
                        "relation": "co_occurs_with",
                        "weight": 0.5,
                        "confidence": 0.50,
                        "chunk_id": chunk_id,
                        "paper_id": paper_id,
                        "arxiv_id": arxiv_id,
                        "section_name": section_name,
                        "page_number": page_number,
                        "evidence_text": text[:180].strip()
                    })

        return relations


# -------------------------------------------------------------------------
# 4. NetworkX Graph Indexer & Disk Persistence
# -------------------------------------------------------------------------

class GraphIndexer:
    """
    Manages constructing, saving, loading, and traversing a NetworkX DiGraph for a corpus.
    Nodes: entity_id, canonical_name, entity_type, aliases, paper_ids, chunk_ids, occurrences
    Edges: source, target, relation, weight, confidence, paper_ids, chunk_ids, section_name, page_number
    """

    @classmethod
    def build_graph(cls, chunks: List[Dict[str, Any]]) -> nx.DiGraph:
        """Constructs a NetworkX DiGraph from a list of chunk data objects."""
        g = nx.DiGraph()

        for chunk in chunks:
            if chunk.get("chunk_type") != "child":
                continue

            content = chunk.get("content", "")
            chunk_id = chunk.get("id", "")
            paper_id = chunk.get("paper_id", "")
            arxiv_id = chunk.get("arxiv_id", "")
            section_name = chunk.get("section_name", "Content")
            page_number = chunk.get("page_number", 1)

            entities = EntityExtractor.extract_entities(content)
            relations = RelationExtractor.extract_relations(
                text=content,
                entities=entities,
                chunk_id=chunk_id,
                paper_id=paper_id,
                arxiv_id=arxiv_id,
                section_name=section_name,
                page_number=page_number
            )

            # Add / update nodes
            for ent in entities:
                cname = ent["canonical_name"]
                etype = ent["entity_type"]
                if not g.has_node(cname):
                    g.add_node(
                        cname,
                        entity_id=cname.lower().replace(" ", "_"),
                        canonical_name=cname,
                        entity_type=etype,
                        aliases=EntityNormalizer.get_aliases(cname),
                        paper_ids=[],
                        chunk_ids=[],
                        occurrences=0
                    )
                node_data = g.nodes[cname]
                node_data["occurrences"] += 1
                if paper_id and paper_id not in node_data["paper_ids"]:
                    node_data["paper_ids"].append(paper_id)
                if chunk_id and chunk_id not in node_data["chunk_ids"]:
                    node_data["chunk_ids"].append(chunk_id)

            # Add / update edges
            for rel in relations:
                src = rel["source"]
                tgt = rel["target"]
                rel_type = rel["relation"]
                weight = rel["weight"]

                if not g.has_node(src) or not g.has_node(tgt):
                    continue

                if g.has_edge(src, tgt):
                    edge_data = g[src][tgt]
                    edge_data["weight"] = round(edge_data["weight"] + weight, 2)
                    if chunk_id and chunk_id not in edge_data["chunk_ids"]:
                        edge_data["chunk_ids"].append(chunk_id)
                    if paper_id and paper_id not in edge_data["paper_ids"]:
                        edge_data["paper_ids"].append(paper_id)
                    if rel_type != "co_occurs_with":
                        edge_data["relation"] = rel_type  # promote to semantic relation
                else:
                    g.add_edge(
                        src,
                        tgt,
                        relation=rel_type,
                        weight=weight,
                        confidence=rel["confidence"],
                        paper_ids=[paper_id] if paper_id else [],
                        chunk_ids=[chunk_id] if chunk_id else [],
                        section_name=section_name,
                        page_number=page_number,
                        evidence_text=rel.get("evidence_text", "")
                    )

        return g

    @classmethod
    def save_graph(cls, g: nx.DiGraph, corpus_id: str, indices_dir: Path) -> Path:
        """Serializes the graph to JSON and binary pickle format on disk."""
        indices_dir.mkdir(parents=True, exist_ok=True)
        json_path = indices_dir / f"{corpus_id}_graph.json"
        pkl_path = indices_dir / f"{corpus_id}_graph.pkl"

        # Prepare JSON serializable dictionary
        data = {
            "corpus_id": corpus_id,
            "directed": True,
            "nodes": [
                {
                    "id": n,
                    **{k: list(v) if isinstance(v, (set, list)) else v for k, v in d.items()}
                }
                for n, d in g.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **{k: list(val) if isinstance(val, (set, list)) else val for k, val in d.items()}
                }
                for u, v, d in g.edges(data=True)
            ]
        }

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GraphIndexer] Failed to write JSON graph: {e}")

        try:
            with open(pkl_path, "wb") as f:
                pickle.dump(g, f)
        except Exception as e:
            print(f"[GraphIndexer] Failed to write pickle graph: {e}")

        return json_path

    @classmethod
    def load_graph(cls, corpus_id: str, indices_dir: Path) -> Optional[nx.DiGraph]:
        """Loads serialized graph from disk (pickle first for speed, JSON as fallback)."""
        pkl_path = indices_dir / f"{corpus_id}_graph.pkl"
        json_path = indices_dir / f"{corpus_id}_graph.json"

        if pkl_path.exists():
            try:
                with open(pkl_path, "rb") as f:
                    g = pickle.load(f)
                    if isinstance(g, (nx.Graph, nx.DiGraph)):
                        return g
            except Exception as e:
                print(f"[GraphIndexer] Pickle load failed, trying JSON: {e}")

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                g = nx.DiGraph()
                for n in data.get("nodes", []):
                    nid = n["id"]
                    attrs = {k: v for k, v in n.items() if k != "id"}
                    g.add_node(nid, **attrs)
                for e in data.get("edges", []):
                    src = e["source"]
                    tgt = e["target"]
                    attrs = {k: v for k, v in e.items() if k not in ("source", "target")}
                    g.add_edge(src, tgt, **attrs)
                return g
            except Exception as e:
                print(f"[GraphIndexer] JSON load failed: {e}")

        return None

    @classmethod
    def multi_hop_traversal(
        cls,
        g: nx.DiGraph,
        query: str,
        top_k_nodes: int = 5,
        max_hops: int = 2
    ) -> Dict[str, Any]:
        """
        Executes bounded 1-hop and 2-hop traversal starting from query-matched entities:
        1. Query -> extract & normalize entities -> match seed nodes in graph
        2. 1-hop traversal with decay weight (0.7)
        3. 2-hop traversal with decay weight (0.4)
        4. Subgraph extraction & node scoring
        5. Map traversed edges to supporting chunks and papers
        """
        if not g or len(g.nodes()) == 0:
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

        # Step 1: Query entity matching
        query_entities = EntityExtractor.extract_entities(query)
        q_lower = query.lower()
        q_tokens = set(re.findall(r"\b[A-Za-z0-9_-]{3,}\b", q_lower))

        seed_scores: Dict[str, float] = {}

        for n, data in g.nodes(data=True):
            n_str = str(n)
            n_lower = n_str.lower()
            aliases = [a.lower() for a in data.get("aliases", [])]

            score = 0.0
            # Exact canonical or alias match
            if any(e["canonical_name"].lower() == n_lower for e in query_entities):
                score += 20.0
            elif any(a in q_lower for a in aliases):
                score += 15.0
            elif n_lower in q_lower:
                score += 12.0
            else:
                # Token overlap
                n_toks = set(re.findall(r"\b[A-Za-z0-9_-]{3,}\b", n_lower))
                overlap = len(q_tokens.intersection(n_toks))
                if overlap > 0:
                    score += overlap * 4.0

            if score > 0:
                # Degree bonus
                deg = g.degree(n)
                score += min(5.0, deg * 0.5)
                seed_scores[n] = score

        # If no seeds matched, pick highest degree central nodes as fallbacks
        if not seed_scores:
            top_deg = sorted(g.nodes(), key=lambda n: g.degree(n), reverse=True)[:top_k_nodes]
            for n in top_deg:
                seed_scores[n] = 1.0

        sorted_seeds = sorted(seed_scores.items(), key=lambda x: x[1], reverse=True)[:top_k_nodes]
        seed_nodes = [s[0] for s in sorted_seeds]

        # Step 2: 1-hop and 2-hop traversal
        visited_nodes: Set[str] = set(seed_nodes)
        node_scores: Dict[str, float] = {s: score for s, score in sorted_seeds}
        traversed_edges: List[Dict[str, Any]] = []
        hop_map: Dict[str, int] = {s: 0 for s in seed_nodes}

        # 1-Hop Expansion
        one_hop_nodes: Set[str] = set()
        for s in seed_nodes:
            # Outgoing & incoming neighbors
            neighbors = list(g.successors(s)) + list(g.predecessors(s))
            for nbr in neighbors:
                if nbr not in visited_nodes:
                    visited_nodes.add(nbr)
                    one_hop_nodes.add(nbr)
                    hop_map[nbr] = 1

                edge_data = g.get_edge_data(s, nbr) or g.get_edge_data(nbr, s) or {}
                rel = edge_data.get("relation", "relates_to")
                weight = float(edge_data.get("weight", 1.0))
                edge_score = node_scores[s] * 0.7 * min(2.0, weight)
                node_scores[nbr] = node_scores.get(nbr, 0.0) + edge_score

                traversed_edges.append({
                    "source": s,
                    "target": nbr,
                    "relation": rel,
                    "hop": 1,
                    "weight": weight,
                    "chunk_ids": edge_data.get("chunk_ids", []),
                    "paper_ids": edge_data.get("paper_ids", []),
                    "section_name": edge_data.get("section_name", "Section"),
                    "page_number": edge_data.get("page_number", 1),
                    "evidence_text": edge_data.get("evidence_text", "")
                })

        # 2-Hop Expansion
        if max_hops >= 2:
            two_hop_candidates = list(one_hop_nodes)[:10]
            for h1 in two_hop_candidates:
                neighbors = list(g.successors(h1)) + list(g.predecessors(h1))
                for nbr in neighbors:
                    if nbr not in visited_nodes:
                        visited_nodes.add(nbr)
                        hop_map[nbr] = 2

                    edge_data = g.get_edge_data(h1, nbr) or g.get_edge_data(nbr, h1) or {}
                    rel = edge_data.get("relation", "relates_to")
                    weight = float(edge_data.get("weight", 1.0))
                    edge_score = node_scores.get(h1, 1.0) * 0.4 * min(2.0, weight)
                    node_scores[nbr] = node_scores.get(nbr, 0.0) + edge_score

                    traversed_edges.append({
                        "source": h1,
                        "target": nbr,
                        "relation": rel,
                        "hop": 2,
                        "weight": weight,
                        "chunk_ids": edge_data.get("chunk_ids", []),
                        "paper_ids": edge_data.get("paper_ids", []),
                        "section_name": edge_data.get("section_name", "Section"),
                        "page_number": edge_data.get("page_number", 1),
                        "evidence_text": edge_data.get("evidence_text", "")
                    })

        # Step 3: Rank results & compile telemetry
        top_ranked_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)[:top_k_nodes * 2]

        all_chunk_ids: List[str] = []
        seen_chunks: Set[str] = set()

        for edge in traversed_edges:
            for cid in edge["chunk_ids"]:
                if cid and cid not in seen_chunks:
                    seen_chunks.add(cid)
                    all_chunk_ids.append(cid)

        for n, _ in top_ranked_nodes:
            for cid in g.nodes[n].get("chunk_ids", []):
                if cid and cid not in seen_chunks:
                    seen_chunks.add(cid)
                    all_chunk_ids.append(cid)

        # Formatted path strings for UI display: e.g. "Transformer ──uses──> Self-Attention"
        formatted_paths = []
        for e in traversed_edges[:12]:
            formatted_paths.append({
                "source": e["source"],
                "relation": e["relation"],
                "target": e["target"],
                "hop": e["hop"],
                "chunk_ids": e["chunk_ids"],
                "section_name": e["section_name"],
                "page_number": e["page_number"],
                "representation": f"{e['source']} ──{e['relation']}──> {e['target']}"
            })

        subgraph_nodes = list(visited_nodes)
        telemetry = {
            "nodes_matched": len(seed_nodes),
            "nodes_traversed": len(visited_nodes),
            "number_of_hops": max_hops if traversed_edges else (1 if one_hop_nodes else 0),
            "edges_traversed": len(traversed_edges),
            "subgraph_size": {
                "nodes": len(subgraph_nodes),
                "edges": len(traversed_edges)
            },
            "retrieved_chunks": len(all_chunk_ids)
        }

        return {
            "matched_nodes": seed_nodes,
            "ranked_nodes": [
                {
                    "entity": n,
                    "score": round(score, 2),
                    "type": g.nodes[n].get("entity_type", "concept"),
                    "hop": hop_map.get(n, 0),
                    "degree": g.degree(n),
                    "chunk_ids": g.nodes[n].get("chunk_ids", [])
                }
                for n, score in top_ranked_nodes
            ],
            "traversed_edges": traversed_edges,
            "paths": formatted_paths,
            "retrieved_chunk_ids": all_chunk_ids,
            "telemetry": telemetry
        }
