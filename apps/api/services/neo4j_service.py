import time
import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from neo4j import GraphDatabase, Driver
from apps.api.core.config import settings

logger = logging.getLogger("neo4j_service")

# Scientific ontology dictionaries for typed extraction
METHOD_PATTERNS = [
    r"\b(Transformer|BERT|GPT(?:-\d)?|RoBERTa|T5|LLaMA(?:-\d)?|Mistral|Claude|Mamba|RWKV|ResNet|Diffusion Model|LoRA|QLoRA|DPR|BM25s?|HNSW|RRF|Reciprocal Rank Fusion|CRAG|FLARE|Self-RAG|AST Chunking|AdamW?|SGD)\b"
]
DATASET_PATTERNS = [
    r"\b(ImageNet|SQuAD|MS MARCO|HotpotQA|TriviaQA|Natural Questions|GLUE|SuperGLUE|GSM8K|HumanEval|MMLU|MATH|Pile|Common Crawl|Wikipedia|ArXiv)\b"
]
METRIC_PATTERNS = [
    r"\b(BLEU(?:-\d)?|ROUGE(?:-[12L])?|Accuracy|F1(?:-Score)?|Precision|Recall|MRR(?:@\d+)?|nDCG(?:@\d+)?|Perplexity|Exact Match|Hit Rate(?:@\d+)?)\b"
]
TASK_PATTERNS = [
    r"\b(Question Answering|Information Retrieval|Text Generation|Summarization|Reasoning|Code Generation|Classification|Semantic Search|Machine Translation)\b"
]
CONCEPT_PATTERNS = [
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b",
    r"\b(Attention Mechanism|Positional Bias|Lost in the Middle|Context Window|Hallucination|Vector Embedding|Cosine Similarity|Knowledge Graph)\b"
]

STOPWORDS = {
    "this", "that", "these", "those", "from", "with", "have", "been", "there", "their",
    "where", "which", "about", "above", "after", "again", "against", "figure", "table",
    "section", "paper", "author", "authors", "result", "results", "using", "based", "shown"
}

class Neo4jService:
    def __init__(self):
        self._driver: Optional[Driver] = None
        self._is_available: Optional[bool] = None
        self._last_check_time: float = 0.0
        self._check_interval: float = 30.0  # re-check availability every 30s if failed

    def get_driver(self) -> Optional[Driver]:
        if not self.is_available():
            return None
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                    connection_timeout=2.0,
                    max_connection_lifetime=300
                )
            except Exception as e:
                logger.warning(f"[Neo4j] Driver initialization failed: {e}")
                self._is_available = False
                return None
        return self._driver

    def is_available(self) -> bool:
        now = time.time()
        if self._is_available is not None and (now - self._last_check_time) < self._check_interval:
            return self._is_available

        self._last_check_time = now
        try:
            if self._driver is None:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                    connection_timeout=2.0,
                    max_connection_lifetime=300
                )
            self._driver.verify_connectivity()
            self._is_available = True
            logger.info(f"[Neo4j] Verified connection to {settings.NEO4J_URI}")
            return True
        except Exception as e:
            self._is_available = False
            logger.info(f"[Neo4j] Graph database unreachable ({e}). Fallback to in-memory NetworkX active.")
            return False

    def init_schema(self):
        driver = self.get_driver()
        if not driver:
            return

        queries = [
            "CREATE CONSTRAINT paper_arxiv IF NOT EXISTS FOR (p:Paper) REQUIRE p.arxiv_id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT method_name IF NOT EXISTS FOR (m:Method) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT dataset_name IF NOT EXISTS FOR (d:Dataset) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT metric_name IF NOT EXISTS FOR (mt:Metric) REQUIRE mt.name IS UNIQUE",
            "CREATE CONSTRAINT task_name IF NOT EXISTS FOR (t:Task) REQUIRE t.name IS UNIQUE"
        ]
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                for q in queries:
                    try:
                        session.run(q)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"[Neo4j] Schema initialization notice: {e}")

    def _extract_typed_entities(self, text: str) -> Dict[str, Set[str]]:
        results: Dict[str, Set[str]] = {
            "methods": set(),
            "datasets": set(),
            "metrics": set(),
            "tasks": set(),
            "concepts": set()
        }

        for pat in METHOD_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip()
                if len(val) > 2 and val.lower() not in STOPWORDS:
                    results["methods"].add(val)

        for pat in DATASET_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip()
                if len(val) > 2 and val.lower() not in STOPWORDS:
                    results["datasets"].add(val)

        for pat in METRIC_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip()
                if len(val) > 1 and val.lower() not in STOPWORDS:
                    results["metrics"].add(val)

        for pat in TASK_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip().title()
                if len(val) > 3 and val.lower() not in STOPWORDS:
                    results["tasks"].add(val)

        for pat in CONCEPT_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip().title()
                if len(val) > 3 and val.lower() not in STOPWORDS:
                    results["concepts"].add(val)

        return results

    def sync_corpus_graph(self, corpus_id: str, chunks_data: List[Dict[str, Any]]):
        """
        Dispatches graph sync asynchronously in a background thread to prevent blocking user queries.
        """
        import threading
        t = threading.Thread(
            target=self._execute_batch_sync,
            args=(corpus_id, chunks_data),
            daemon=True
        )
        t.start()

    def _execute_batch_sync(self, corpus_id: str, chunks_data: List[Dict[str, Any]]):
        driver = self.get_driver()
        if not driver or not chunks_data:
            return

        self.init_schema()

        # Build vectorized batches for high-speed single-query ingestion
        chunks_batch = []
        methods_batch = []
        datasets_batch = []
        metrics_batch = []
        concepts_batch = []
        relations_batch = []

        for chunk in chunks_data:
            c_id = chunk["id"]
            paper_id = chunk.get("paper_id", "")
            arxiv_id = chunk.get("arxiv_id", "")
            paper_title = chunk.get("paper_title", "Research Paper")
            page_number = chunk.get("page_number", 1)
            section_name = chunk.get("section_name", "")
            content = chunk.get("content", "")

            chunks_batch.append({
                "c_id": c_id,
                "arxiv_id": arxiv_id,
                "paper_id": paper_id,
                "paper_title": paper_title,
                "corpus_id": corpus_id,
                "page_number": page_number,
                "section_name": section_name,
                "content_preview": content[:200]
            })

            typed_ents = self._extract_typed_entities(content)
            for m_name in list(typed_ents["methods"])[:5]:
                methods_batch.append({"name": m_name, "c_id": c_id, "arxiv_id": arxiv_id})
            for d_name in list(typed_ents["datasets"])[:4]:
                datasets_batch.append({"name": d_name, "c_id": c_id, "arxiv_id": arxiv_id})
            for mt_name in list(typed_ents["metrics"])[:4]:
                metrics_batch.append({"name": mt_name, "c_id": c_id, "arxiv_id": arxiv_id})

            ent_list = list(typed_ents["concepts"])[:6]
            for ent in ent_list:
                concepts_batch.append({"name": ent, "c_id": c_id, "corpus_id": corpus_id})

            for i in range(len(ent_list)):
                for j in range(i + 1, min(len(ent_list), i + 3)):
                    relations_batch.append({
                        "e1": ent_list[i],
                        "e2": ent_list[j],
                        "corpus_id": corpus_id,
                        "arxiv_id": arxiv_id
                    })

        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                # 1. Batch upsert Papers and Chunks
                session.run("""
                    UNWIND $batch AS item
                    MERGE (p:Paper {arxiv_id: item.arxiv_id})
                    ON CREATE SET p.id = item.paper_id, p.title = item.paper_title
                    MERGE (c:Chunk {id: item.c_id})
                    ON CREATE SET c.corpus_id = item.corpus_id,
                                  c.paper_id = item.paper_id,
                                  c.page_number = item.page_number,
                                  c.section_name = item.section_name,
                                  c.content_preview = item.content_preview
                    MERGE (c)-[:PART_OF_PAPER]->(p)
                """, batch=chunks_batch)

                # 2. Batch upsert Methods
                if methods_batch:
                    session.run("""
                        UNWIND $batch AS item
                        MERGE (m:Method {name: item.name})
                        WITH m, item
                        MATCH (c:Chunk {id: item.c_id}), (p:Paper {arxiv_id: item.arxiv_id})
                        MERGE (c)-[:MENTIONS]->(m)
                        MERGE (p)-[:USES_METHOD]->(m)
                    """, batch=methods_batch)

                # 3. Batch upsert Datasets
                if datasets_batch:
                    session.run("""
                        UNWIND $batch AS item
                        MERGE (d:Dataset {name: item.name})
                        WITH d, item
                        MATCH (c:Chunk {id: item.c_id}), (p:Paper {arxiv_id: item.arxiv_id})
                        MERGE (c)-[:MENTIONS]->(d)
                        MERGE (p)-[:EVALUATED_ON]->(d)
                    """, batch=datasets_batch)

                # 4. Batch upsert Metrics
                if metrics_batch:
                    session.run("""
                        UNWIND $batch AS item
                        MERGE (mt:Metric {name: item.name})
                        WITH mt, item
                        MATCH (c:Chunk {id: item.c_id}), (p:Paper {arxiv_id: item.arxiv_id})
                        MERGE (c)-[:MENTIONS]->(mt)
                        MERGE (p)-[:REPORTS_METRIC]->(mt)
                    """, batch=metrics_batch)

                # 5. Batch upsert Concepts
                if concepts_batch:
                    session.run("""
                        UNWIND $batch AS item
                        MERGE (e:Entity {name: item.name})
                        ON CREATE SET e.type = 'concept'
                        WITH e, item
                        MATCH (c:Chunk {id: item.c_id})
                        MERGE (e)-[r:MENTIONED_IN]->(c)
                        ON CREATE SET r.corpus_id = item.corpus_id, r.weight = 1
                        ON MATCH SET r.weight = r.weight + 1
                    """, batch=concepts_batch)

                # 6. Batch upsert Relations
                if relations_batch:
                    session.run("""
                        UNWIND $batch AS item
                        MATCH (e1:Entity {name: item.e1}), (e2:Entity {name: item.e2})
                        MERGE (e1)-[r:RELATES_TO]-(e2)
                        ON CREATE SET r.corpus_id = item.corpus_id, r.weight = 1, r.paper = item.arxiv_id
                        ON MATCH SET r.weight = r.weight + 1
                    """, batch=relations_batch)

                logger.info(f"[Neo4j] Vectorized background batch synced {len(chunks_batch)} chunks to knowledge graph.")
        except Exception as e:
            logger.warning(f"[Neo4j] Error during batch graph ingestion: {e}")

    def search_graph(self, corpus_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Bounded multi-hop traversal with path scoring and typed entity retrieval in Neo4j.
        """
        driver = self.get_driver()
        if not driver:
            return []

        q_terms = [w.strip() for w in query.split() if len(w.strip()) > 2 and w.lower() not in STOPWORDS]
        if not q_terms:
            return []

        results = []
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                # 1. Bounded 2-hop traversal query with typed entities and path weight
                cypher = """
                UNWIND $q_terms AS term
                MATCH (n)
                WHERE (n:Entity OR n:Method OR n:Dataset OR n:Metric)
                  AND (toLower(n.name) CONTAINS toLower(term) OR toLower(term) CONTAINS toLower(n.name))
                OPTIONAL MATCH (n)-[r:RELATES_TO|USES_METHOD|EVALUATED_ON|REPORTS_METRIC*1..2]-(nbr)
                OPTIONAL MATCH (n)-[:MENTIONED_IN|MENTIONS]-(c:Chunk)
                WHERE c.corpus_id = $corpus_id
                WITH n,
                     labels(n)[0] AS node_type,
                     collect(DISTINCT nbr.name)[..8] AS neighbors,
                     collect(DISTINCT c.id)[..6] AS chunk_ids,
                     count(DISTINCT nbr) AS degree
                RETURN DISTINCT n.name AS entity,
                                node_type,
                                neighbors,
                                chunk_ids,
                                degree,
                                (degree * 1.5 + size(chunk_ids) * 2.0) AS path_score
                ORDER BY path_score DESC, degree DESC
                LIMIT $top_k
                """
                records = session.run(cypher, q_terms=q_terms, corpus_id=corpus_id, top_k=top_k)
                for rec in records:
                    results.append({
                        "entity": rec["entity"],
                        "type": rec["node_type"],
                        "neighbors": rec["neighbors"],
                        "chunk_ids": rec["chunk_ids"],
                        "degree": rec["degree"],
                        "path_score": round(float(rec.get("path_score", 1.0)), 2)
                    })
        except Exception as e:
            logger.warning(f"[Neo4j] search_graph query error: {e}")

        return results

    def get_community_clusters(self, corpus_id: str, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves dominant community clusters across the knowledge graph for high-level thematic queries.
        """
        driver = self.get_driver()
        if not driver:
            return []

        communities = []
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                cypher = """
                MATCH (p:Paper)<-[:PART_OF_PAPER]-(c:Chunk {corpus_id: $corpus_id})
                MATCH (c)-[:MENTIONS|MENTIONED_IN]-(e)
                WITH p.title AS paper, p.arxiv_id AS arxiv_id, collect(DISTINCT e.name)[..6] AS key_entities, collect(DISTINCT c.id)[..4] AS chunk_ids
                RETURN paper, arxiv_id, key_entities, chunk_ids
                ORDER BY size(key_entities) DESC
                LIMIT $limit
                """
                records = session.run(cypher, corpus_id=corpus_id, limit=limit)
                for rec in records:
                    communities.append({
                        "theme": rec["paper"],
                        "arxiv_id": rec["arxiv_id"],
                        "entities": rec["key_entities"],
                        "chunk_ids": rec["chunk_ids"]
                    })
        except Exception as e:
            logger.warning(f"[Neo4j] get_community_clusters error: {e}")
        return communities

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

neo4j_service = Neo4jService()
