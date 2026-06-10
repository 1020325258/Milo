"""
依赖注入

提供 FastAPI 依赖注入函数，用于数据库会话、服务实例等。
"""

from typing import Annotated, Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.elasticsearch import get_es_client
from app.services.embedding.base import BaseEmbeddingService
from app.services.embedding.dashscope import DashScopeEmbeddingService
from app.services.retrieval.es_client import ESClient
from app.services.retrieval.reranker import BaseReranker, DashScopeReranker
from app.services.retrieval.retriever import Retriever


async def get_current_user_id(
    x_user_id: str = Header(
        description="调用者的用户 ID。临时基于 header 的身份标识，后续将替换为 JWT 认证。",
    ),
) -> str:
    """从 X-User-ID 请求头获取当前用户 ID。

    Args:
        x_user_id: X-User-ID header 值

    Returns:
        用户 ID 字符串

    Raises:
        HTTPException: header 缺失或为空时返回 401
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header is required.",
        )
    return x_user_id


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
UserID = Annotated[str, Depends(get_current_user_id)]
EmbeddingService = Annotated[BaseEmbeddingService, Depends(get_embedding_service)]
RerankerService = Annotated[BaseReranker, Depends(get_reranker)]
ESService = Annotated[ESClient, Depends(get_es_service)]
RetrieverService = Annotated[Retriever, Depends(get_retriever)]
