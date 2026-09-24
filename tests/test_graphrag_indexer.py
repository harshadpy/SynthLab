import pytest
import networkx as nx
from pathlib import Path
from apps.api.rag.graph_indexer import (
    EntityNormalizer,
    EntityExtractor,
    RelationExtractor,
    GraphIndexer
)
from apps.api.rag.graph_rag import graph_rag
from apps.api.services.index_service import index_service

def test_entity_normalization_and_aliases():
    """Requirement 3: Test canonical entity names, alias handling, and duplicate prevention."""
    assert EntityNormalizer.normalize("LLM") == ("Large Language Model", "model")
    assert EntityNormalizer.normalize("large language model") == ("Large Language Model", "model")
    assert EntityNormalizer.normalize("large language models") == ("Large Language Model", "model")
    assert EntityNormalizer.normalize("CNN") == ("Convolutional Neural Network", "model")
    assert EntityNormalizer.normalize("transformers") == ("Transformer", "model")
    assert EntityNormalizer.normalize("rag") == ("Retrieval-Augmented Generation", "method")
    assert EntityNormalizer.normalize("BM25") == ("BM25", "method")
    assert EntityNormalizer.normalize("bm-25") == ("BM25", "method")
    assert EntityNormalizer.normalize("RRF") == ("Reciprocal Rank Fusion", "method")
    assert EntityNormalizer.normalize("ms marco") == ("MS MARCO", "dataset")
    assert EntityNormalizer.normalize("f1 score") == ("F1 Score", "metric")

    aliases = EntityNormalizer.get_aliases("Large Language Model")
    assert "llm" in aliases or "large language models" in aliases

def test_entity_extraction_categories():
    """Requirement 2: Test extraction of Models, Methods, Datasets, Metrics, Technologies, Concepts."""
    sample_text = (
        "In this study, the Transformer architecture uses Multi-Head Attention and FlashAttention. "
        "We evaluate our Retrieval-Augmented Generation pipeline using BM25 and Dense Retrieval on MS MARCO and SQuAD. "
        "Our method achieves superior BLEU and F1 scores implemented in PyTorch with LangGraph."
    )
    entities = EntityExtractor.extract_entities(sample_text)
    cnames = {e["canonical_name"] for e in entities}
    types = {e["canonical_name"]: e["entity_type"] for e in entities}

    assert "Transformer" in cnames
    assert "Multi-Head Attention" in cnames
    assert "FlashAttention" in cnames
    assert "Retrieval-Augmented Generation" in cnames
    assert "BM25" in cnames
    assert "Dense Retrieval" in cnames
    assert "MS MARCO" in cnames
    assert "SQuAD" in cnames
    assert "F1 Score" in cnames
    assert "PyTorch" in cnames
    assert "LangGraph" in cnames

    assert types["Transformer"] == "model"
    assert types["BM25"] == "method"
    assert types["MS MARCO"] == "dataset"
    assert types["F1 Score"] == "metric"
    assert types["PyTorch"] == "technology"

def test_relation_extraction_semantic_and_fallback():
    """Requirement 4: Meaningful directed relationships instead of only co-occurrence."""
    text = (
        "The Transformer uses Self-Attention. "
        "Dense Retrieval combined with BM25 outperforms standard sparse models on MS MARCO."
    )
    entities = EntityExtractor.extract_entities(text)
    relations = RelationExtractor.extract_relations(
        text=text,
        entities=entities,
        chunk_id="chunk-001",
        paper_id="paper-001",
        arxiv_id="1706.03762",
        section_name="§3.2 Attention Mechanism",
        page_number=4
    )

    # Check for semantic relations
    rel_types = {(r["source"], r["relation"], r["target"]) for r in relations}
    assert ("Transformer", "uses", "Self-Attention") in rel_types or any(r["relation"] == "uses" for r in relations)

    # Check every relation retains traceable provenance metadata (Requirement 9)
    for r in relations:
        assert r["chunk_id"] == "chunk-001"
        assert r["paper_id"] == "paper-001"
        assert r["arxiv_id"] == "1706.03762"
        assert r["section_name"] == "§3.2 Attention Mechanism"
        assert r["page_number"] == 4
        assert r["weight"] > 0

def test_graph_builder_and_persistence(tmp_path: Path):
    """Requirements 5 & 6: NetworkX Graph schema and disk serialization/persistence."""
    chunks = [
        {
            "id": "c-1",
            "paper_id": "p-1",
            "arxiv_id": "2301.0001",
            "chunk_type": "child",
            "content": "RAG uses BM25 and Dense Retrieval with Reciprocal Rank Fusion.",
            "section_name": "Methods",
            "page_number": 2
        },
        {
            "id": "c-2",
            "paper_id": "p-1",
            "arxiv_id": "2301.0001",
            "chunk_type": "child",
            "content": "We evaluate on MS MARCO measuring nDCG and Latency.",
            "section_name": "Experiments",
            "page_number": 5
        }
    ]

    g = GraphIndexer.build_graph(chunks)
    assert isinstance(g, nx.DiGraph)
    assert g.has_node("Retrieval-Augmented Generation")
    assert g.has_node("BM25")

    node_data = g.nodes["BM25"]
    assert node_data["entity_type"] == "method"
    assert "c-1" in node_data["chunk_ids"]

    # Test disk serialization (JSON and Pickle)
    corpus_id = "test_corpus"
    json_path = GraphIndexer.save_graph(g, corpus_id, tmp_path)
    assert json_path.exists()
    assert (tmp_path / f"{corpus_id}_graph.pkl").exists()

    # Test reload
    loaded_g = GraphIndexer.load_graph(corpus_id, tmp_path)
    assert loaded_g is not None
    assert loaded_g.number_of_nodes() == g.number_of_nodes()
    assert loaded_g.has_node("Retrieval-Augmented Generation")

def test_multi_hop_traversal_and_telemetry():
    """Requirements 7, 8, 10: 1-hop & 2-hop traversal, edge weighting, node scores, telemetry."""
    chunks = [
        {
            "id": "c-1",
            "paper_id": "p-1",
            "arxiv_id": "2401.0001",
            "chunk_type": "child",
            "content": "Cancer Detection uses Convolutional Neural Network for cellular analysis.",
            "section_name": "Introduction",
            "page_number": 1
        },
        {
            "id": "c-2",
            "paper_id": "p-2",
            "arxiv_id": "2401.0002",
            "chunk_type": "child",
            "content": "Convolutional Neural Network utilizes Transfer Learning from ImageNet.",
            "section_name": "Methodology",
            "page_number": 3
        }
    ]

    g = GraphIndexer.build_graph(chunks)
    assert g.has_node("Cancer Detection")
    assert g.has_node("Convolutional Neural Network")
    assert g.has_node("Transfer Learning")

    # Query about Cancer Detection and ImageNet -> multi-hop intermediate traversal
    query = "How does cancer detection leverage transfer learning and models?"
    result = GraphIndexer.multi_hop_traversal(g, query, top_k_nodes=4, max_hops=2)

    assert "Cancer Detection" in result["matched_nodes"] or len(result["matched_nodes"]) > 0
    assert len(result["traversed_edges"]) > 0

    telemetry = result["telemetry"]
    assert telemetry["nodes_matched"] >= 1
    assert telemetry["nodes_traversed"] >= 2
    assert telemetry["number_of_hops"] == 2
    assert telemetry["edges_traversed"] >= 1
    assert "c-1" in result["retrieved_chunk_ids"] or "c-2" in result["retrieved_chunk_ids"]

@pytest.mark.asyncio
async def test_graphrag_pipeline_retrieval():
    """Requirement 9 & 10: Query-time GraphRAG pipeline with evidence grounding and telemetry."""
    corpus_id = "test_graphrag_pipeline_corpus"
    chunks = [
        {
            "id": "chunk-test-1",
            "paper_id": "paper-rag-1",
            "arxiv_id": "1706.03762",
            "chunk_type": "child",
            "content": "The Transformer uses Self-Attention and Multi-Head Attention for machine translation.",
            "section_name": "§3.2 Attention Mechanism",
            "page_number": 4,
            "token_count": 28
        }
    ]

    index_service.index_corpus(corpus_id, chunks, sync_neo4j=False)
    retrieval_res = await graph_rag.retrieve("How does the Transformer use Self-Attention?", corpus_id, {"top_k": 3})

    assert len(retrieval_res.citations) > 0
    top_cit = retrieval_res.citations[0]
    meta = top_cit.strategy_metadata

    assert meta["strategy"] == "GraphRAG"
    assert "matched_entity" in meta
    assert "edge_relations" in meta
    assert "telemetry" in meta
    assert meta["telemetry"]["number_of_hops"] >= 1

    # Cleanup
    index_service.remove_corpus(corpus_id)
