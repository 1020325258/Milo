"""
Embedding 服务模块

提供文本向量化功能。
"""

from app.services.embedding.base import BaseEmbeddingService
from app.services.embedding.dashscope import DashScopeEmbeddingService

__all__ = ["BaseEmbeddingService", "DashScopeEmbeddingService"]
