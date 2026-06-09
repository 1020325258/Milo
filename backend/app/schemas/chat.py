"""
对话 Schema

定义对话相关的请求和响应模型。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求"""

    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    conversation_id: Optional[int] = Field(None, description="对话 ID")
    knowledge_base_id: Optional[int] = Field(None, description="知识库 ID")
    stream: bool = Field(True, description="是否流式响应")


class Reference(BaseModel):
    """引用"""

    chunk_id: str = Field(..., description="切片 ID")
    document_id: int = Field(..., description="文档 ID")
    document_name: str = Field(..., description="文档名称")
    content: str = Field(..., description="引用内容")
    relevance_score: float = Field(..., description="相关性分数")


class MessageResponse(BaseModel):
    """消息响应"""

    id: int = Field(..., description="消息 ID")
    role: str = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    thinking_content: Optional[str] = Field(None, description="思考内容")
    references: Optional[dict] = Field(None, description="引用列表")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """对话响应"""

    conversation_id: int = Field(..., description="对话 ID")
    message: MessageResponse = Field(..., description="助手消息")
