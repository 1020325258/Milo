"""
检索器

提供完整的检索流程：向量检索 + BM25 + RRF + Rerank。
"""

from typing import List, Optional

from app.core.config import settings
from app.services.embedding.base import BaseEmbeddingService
from app.services.retrieval.es_client import ESClient
from app.services.retrieval.reranker import BaseReranker, RerankResult


class Retriever:
    """检索器"""

    def __init__(
        self,
        es: ESClient,
        embedding: BaseEmbeddingService,
        reranker: BaseReranker,
    ) -> None:
        """
        初始化检索器

        Args:
            es: ES 客户端
            embedding: Embedding 服务
            reranker: Rerank 服务
        """
        self.es = es
        self.embedding = embedding
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
        use_rerank: bool = True,
    ) -> List[RerankResult]:
        """
        执行检索

        Args:
            query: 查询文本
            knowledge_base_id: 知识库 ID 过滤
            document_id: 文档 ID 过滤
            top_k: 返回数量
            use_rerank: 是否使用 Rerank

        Returns:
            检索结果列表
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K

        # 向量化查询
        query_embedding = self.embedding.embed_query(query)

        # 混合检索
        results = self.es.search_hybrid(
            query_text=query,
            embedding=query_embedding,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            rrf_k=settings.RRF_K,
        )

        # Rerank（暂时禁用，因为 API 权限问题）
        # if use_rerank and results:
        #     reranked = self.reranker.rerank(
        #         query=query,
        #         results=results,
        #         top_n=settings.RERANK_TOP_K,
        #     )
        #     return reranked

        # 不使用 Rerank，转换为 RerankResult
        return [
            RerankResult(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                knowledge_base_id=r["knowledge_base_id"],
                content=r["content"],
                metadata=r.get("metadata", {}),
                original_score=r.get("score", 0),
                rerank_score=r.get("score", 0),
            )
            for r in results
        ]

    def retrieve_by_vector(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[dict]:
        """
        仅向量检索

        Args:
            query: 查询文本
            knowledge_base_id: 知识库 ID 过滤
            document_id: 文档 ID 过滤
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K

        query_embedding = self.embedding.embed_query(query)

        return self.es.search_vector(
            embedding=query_embedding,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

    def retrieve_by_bm25(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[dict]:
        """
        仅 BM25 检索

        Args:
            query: 查询文本
            knowledge_base_id: 知识库 ID 过滤
            document_id: 文档 ID 过滤
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K

        return self.es.search_bm25(
            query_text=query,
            top_k=top_k,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )
