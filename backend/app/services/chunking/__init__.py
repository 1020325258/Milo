"""
切片服务模块

提供文档切片功能，支持基于文档结构的智能切片。
"""

from app.services.chunking.chunker import BaseChunker, Chunk
from app.services.chunking.smart_chunker import SmartChunker

__all__ = ["BaseChunker", "Chunk", "SmartChunker"]
