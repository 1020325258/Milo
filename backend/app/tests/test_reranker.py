"""
Rerank 服务单元测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.retrieval.reranker import DashScopeReranker, RerankResult


class TestDashScopeReranker:
    """DashScope Rerank 服务测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.reranker = DashScopeReranker()

    @patch("app.services.retrieval.reranker.dashscope_client")
    def test_rerank(self, mock_client: MagicMock) -> None:
        """测试重排序"""
        # Mock 返回值
        mock_client.rerank_texts.return_value = [
            {"index": 1, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.85},
        ]

        results = [
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

        reranked = self.reranker.rerank(
            query="测试查询",
            results=results,
            top_n=2,
        )

        assert len(reranked) == 2
        assert reranked[0].chunk_id == "chunk_002"
        assert reranked[0].rerank_score == 0.95
        assert reranked[1].chunk_id == "chunk_001"
        assert reranked[1].rerank_score == 0.85

    @patch("app.services.retrieval.reranker.dashscope_client")
    def test_rerank_empty_results(self, mock_client: MagicMock) -> None:
        """测试空结果重排序"""
        reranked = self.reranker.rerank(
            query="测试查询",
            results=[],
        )

        assert reranked == []
        mock_client.rerank_texts.assert_not_called()

    @patch("app.services.retrieval.reranker.dashscope_client")
    def test_rerank_with_top_n(self, mock_client: MagicMock) -> None:
        """测试指定 top_n"""
        mock_client.rerank_texts.return_value = [
            {"index": 0, "relevance_score": 0.9},
        ]

        results = [
            {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "knowledge_base_id": "kb_001",
                "content": "内容1",
                "metadata": {},
                "score": 0.8,
            },
        ]

        reranked = self.reranker.rerank(
            query="测试查询",
            results=results,
            top_n=1,
        )

        assert len(reranked) == 1
        mock_client.rerank_texts.assert_called_once_with(
            query="测试查询",
            documents=["内容1"],
            top_n=1,
        )
