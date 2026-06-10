"""
DashScope Embedding 服务

使用 DashScope API 进行文本向量化。
"""

from typing import List

from app.core.config import settings
from app.core.dashscope import dashscope_client
from app.services.embedding.base import BaseEmbeddingService


class DashScopeEmbeddingService(BaseEmbeddingService):
    """DashScope Embedding 服务"""

    def __init__(self) -> None:
        """初始化服务"""
        self._dimension = settings.EMBEDDING_DIMENSION

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not texts:
            return []

        # DashScope API 限制每次最多 10 条
        batch_size = 10
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = dashscope_client.embed_texts(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        查询文本向量化

        Args:
            query: 查询文本

        Returns:
            向量
        """
        embeddings = self.embed_texts([query])
        return embeddings[0] if embeddings else []

    def get_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            向量维度
        """
        return self._dimension
