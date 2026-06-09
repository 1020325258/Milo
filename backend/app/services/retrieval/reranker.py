"""
Rerank 服务

提供检索结果重排序功能。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.core.dashscope import dashscope_client


@dataclass
class RerankResult:
    """重排序结果"""

    chunk_id: str
    document_id: str
    knowledge_base_id: str
    content: str
    metadata: dict
    original_score: float
    rerank_score: float


class BaseReranker(ABC):
    """Rerank 服务基类"""

    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[dict],
        top_n: Optional[int] = None,
    ) -> List[RerankResult]:
        """
        对检索结果进行重排序

        Args:
            query: 查询文本
            results: 检索结果列表
            top_n: 返回前 N 个结果

        Returns:
            重排序后的结果列表
        """
        pass


class DashScopeReranker(BaseReranker):
    """DashScope Rerank 服务"""

    def rerank(
        self,
        query: str,
        results: List[dict],
        top_n: Optional[int] = None,
    ) -> List[RerankResult]:
        """
        对检索结果进行重排序

        Args:
            query: 查询文本
            results: 检索结果列表
            top_n: 返回前 N 个结果

        Returns:
            重排序后的结果列表
        """
        if not results:
            return []

        top_n = top_n or settings.RERANK_TOP_K

        # 提取文档内容
        documents = [r["content"] for r in results]

        # 调用 DashScope Rerank API
        rerank_results = dashscope_client.rerank_texts(
            query=query,
            documents=documents,
            top_n=top_n,
        )

        # 构建结果
        reranked = []
        for rerank_result in rerank_results:
            idx = rerank_result["index"]
            original = results[idx]

            reranked.append(RerankResult(
                chunk_id=original["chunk_id"],
                document_id=original["document_id"],
                knowledge_base_id=original["knowledge_base_id"],
                content=original["content"],
                metadata=original.get("metadata", {}),
                original_score=original.get("score", 0),
                rerank_score=rerank_result["relevance_score"],
            ))

        return reranked
