"""
文档 Schema

定义文档相关的请求和响应模型。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    """文档上传请求"""

    knowledge_base_id: int = Field(..., description="知识库 ID")


class DocumentResponse(BaseModel):
    """文档响应"""

    id: int = Field(..., description="文档 ID")
    knowledge_base_id: int = Field(..., description="知识库 ID")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小")
    status: str = Field(..., description="处理状态")
    chunk_count: int = Field(0, description="切片数量")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """文档列表响应"""

    items: List[DocumentResponse] = Field(..., description="文档列表")
    total: int = Field(..., description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页数量")
