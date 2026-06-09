"""
检索器单元测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.retrieval.reranker import RerankResult
from app.services.retrieval.retriever import Retriever


class TestRetriever:
    """检索器测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.mock_es = MagicMock()
        self.mock_embedding = MagicMock()
        self.mock_reranker = MagicMock()

        self.retriever = Retriever(
            es=self.mock_es,
            embedding=self.mock_embedding,
            reranker=self.mock_reranker,
        )

    def test_retrieve_with_rerank(self) -> None:
        """测试带 Rerank 的检索"""
        # Mock 向量化
        self.mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]

        # Mock 混合检索
        self.mock_es.search_hybrid.return_value = [
            {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "knowledge_base_id": "kb_001",
                "content": "内容1",
                "metadata": {},
                "score": 0.8,
            },
            {
                "chunk_id": "chunk_002",
                "document_id": "doc_002",
                "knowledge_base_id": "kb_001",
                "content": "内容2",
                "metadata": {},
                "score": 0.7,
            },
        ]

        # Mock Rerank
        self.mock_reranker.rerank.return_value = [
            RerankResult(
                chunk_id="chunk_002",
                document_id="doc_002",
                knowledge_base_id="kb_001",
                content="内容2",
                metadata={},
                original_score=0.7,
                rerank_score=0.95,
            ),
            RerankResult(
                chunk_id="chunk_001",
                document_id="doc_001",
                knowledge_base_id="kb_001",
                content="内容1",
                metadata={},
                original_score=0.8,
                rerank_score=0.85,
            ),
        ]

        results = self.retriever.retrieve(
            query="测试查询",
            knowledge_base_id="kb_001",
            top_k=10,
            use_rerank=True,
        )

        assert len(results) == 2
        assert results[0].chunk_id == "chunk_002"
        assert results[0].rerank_score == 0.95

    def test_retrieve_without_rerank(self) -> None:
        """测试不带 Rerank 的检索"""
        # Mock 向量化
        self.mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]

        # Mock 混合检索
        self.mock_es.search_hybrid.return_value = [
            {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "knowledge_base_id": "kb_001",
                "content": "内容1",
                "metadata": {},
                "score": 0.8,
            },
        ]

        results = self.retriever.retrieve(
            query="测试查询",
            use_rerank=False,
        )

        assert len(results) == 1
        assert results[0].chunk_id == "chunk_001"
        assert results[0].rerank_score == 0.8

    def test_retrieve_by_vector(self) -> None:
        """测试向量检索"""
        self.mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        self.mock_es.search_vector.return_value = [
            {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "knowledge_base_id": "kb_001",
                "content": "内容1",
                "metadata": {},
                "score": 0.9,
            },
        ]

        results = self.retriever.retrieve_by_vector(
            query="测试查询",
            top_k=10,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_001"

    def test_retrieve_by_bm25(self) -> None:
        """测试 BM25 检索"""
        self.mock_es.search_bm25.return_value = [
            {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "knowledge_base_id": "kb_001",
                "content": "内容1",
                "metadata": {},
                "score": 1.5,
            },
        ]

        results = self.retriever.retrieve_by_bm25(
            query="测试查询",
            top_k=10,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_001"
        assert results[0]["score"] == 1.5
