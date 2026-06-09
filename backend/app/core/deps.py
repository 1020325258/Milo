"""
依赖注入

提供 FastAPI 依赖注入函数，用于数据库会话、服务实例等。
"""

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.elasticsearch import get_es_client
from app.services.embedding.base import BaseEmbeddingService
from app.services.embedding.dashscope import DashScopeEmbeddingService
from app.services.retrieval.es_client import ESClient
from app.services.retrieval.reranker import BaseReranker, DashScopeReranker
from app.services.retrieval.retriever import Retriever


def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    yield from get_db()


def get_embedding_service() -> BaseEmbeddingService:
    """获取 Embedding 服务"""
    return DashScopeEmbeddingService()


def get_reranker() -> BaseReranker:
    """获取 Rerank 服务"""
    return DashScopeReranker()


def get_es_service() -> ESClient:
    """获取 ES 客户端"""
    return get_es_client()


def get_retriever(
    es: Annotated[ESClient, Depends(get_es_service)],
    embedding: Annotated[BaseEmbeddingService, Depends(get_embedding_service)],
    reranker: Annotated[BaseReranker, Depends(get_reranker)],
) -> Retriever:
    """获取检索服务"""
    return Retriever(es=es, embedding=embedding, reranker=reranker)


# 类型别名
DBSession = Annotated[Session, Depends(get_db_session)]
EmbeddingService = Annotated[BaseEmbeddingService, Depends(get_embedding_service)]
RerankerService = Annotated[BaseReranker, Depends(get_reranker)]
ESService = Annotated[ESClient, Depends(get_es_service)]
RetrieverService = Annotated[Retriever, Depends(get_retriever)]
