"""
知识库 Schema

定义知识库相关的请求和响应模型。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""

    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, max_length=1000, description="知识库描述")
    embedding_model: str = Field(
        default="text-embedding-v3",
        description="Embedding 模型",
    )


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, max_length=1000, description="知识库描述")
    embedding_model: Optional[str] = Field(None, description="Embedding 模型")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""

    id: int = Field(..., description="知识库 ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    embedding_model: str = Field(..., description="Embedding 模型")
    document_count: int = Field(0, description="文档数量")
    chunk_count: int = Field(0, description="切片数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class KnowledgeBaseList(BaseModel):
    """知识库列表响应"""

    items: List[KnowledgeBaseResponse] = Field(..., description="知识库列表")
    total: int = Field(..., description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页数量")
