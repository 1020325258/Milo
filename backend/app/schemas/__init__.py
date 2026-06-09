"""
Pydantic Schema 模块

定义请求和响应的数据模型。
"""

from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.schemas.document import DocumentResponse, DocumentUpload
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse

__all__ = [
    "KnowledgeBaseCreate",
    "KnowledgeBaseResponse",
    "KnowledgeBaseUpdate",
    "DocumentResponse",
    "DocumentUpload",
    "ChatRequest",
    "ChatResponse",
    "MessageResponse",
]
