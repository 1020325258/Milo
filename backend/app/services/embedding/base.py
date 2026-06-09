"""
Embedding 服务基类

定义文本向量化的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingService(ABC):
    """Embedding 服务基类"""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """
        查询文本向量化

        Args:
            query: 查询文本

        Returns:
            向量
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            向量维度
        """
        pass
