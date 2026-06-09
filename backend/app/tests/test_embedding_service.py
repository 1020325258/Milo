"""
Embedding 服务单元测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.embedding.dashscope import DashScopeEmbeddingService


class TestDashScopeEmbeddingService:
    """DashScope Embedding 服务测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.service = DashScopeEmbeddingService()

    def test_get_dimension(self) -> None:
        """测试获取向量维度"""
        dimension = self.service.get_dimension()
        assert dimension == 1024

    @patch("app.services.embedding.dashscope.dashscope_client")
    def test_embed_texts(self, mock_client: MagicMock) -> None:
        """测试批量文本向量化"""
        # Mock 返回值
        mock_client.embed_texts.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        texts = ["文本1", "文本2"]
        embeddings = self.service.embed_texts(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3
        mock_client.embed_texts.assert_called_once_with(texts)

    @patch("app.services.embedding.dashscope.dashscope_client")
    def test_embed_query(self, mock_client: MagicMock) -> None:
        """测试查询文本向量化"""
        # Mock 返回值
        mock_client.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        embedding = self.service.embed_query("查询文本")

        assert len(embedding) == 3
        mock_client.embed_texts.assert_called_once_with(["查询文本"])

    @patch("app.services.embedding.dashscope.dashscope_client")
    def test_embed_texts_empty(self, mock_client: MagicMock) -> None:
        """测试空文本列表"""
        embeddings = self.service.embed_texts([])

        assert embeddings == []
        mock_client.embed_texts.assert_not_called()

    @patch("app.services.embedding.dashscope.dashscope_client")
    def test_embed_texts_large_batch(self, mock_client: MagicMock) -> None:
        """测试大批量文本"""
        # Mock 返回值
        mock_client.embed_texts.return_value = [[0.1] * 3] * 25

        texts = ["文本"] * 30
        embeddings = self.service.embed_texts(texts)

        # 应该分两次调用
        assert mock_client.embed_texts.call_count == 2
        assert len(embeddings) == 30
