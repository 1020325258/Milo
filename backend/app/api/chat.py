"""
对话 API

提供对话的 RESTful 接口，支持流式响应。
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import DBSession, ESService, EmbeddingService, RetrieverService
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.agent.service import AgentService
from app.services.conversation.service import ConversationService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: DBSession,
    retriever: RetrieverService,
    embedding: EmbeddingService,
) -> ChatResponse:
    """
    对话

    Args:
        request: 对话请求
        db: 数据库会话
        retriever: 检索服务
        embedding: Embedding 服务

    Returns:
        对话响应
    """
    conversation_service = ConversationService(db)
    agent_service = AgentService(retriever, embedding)

    # 获取或创建对话
    if request.conversation_id:
        conversation = conversation_service.get_by_id(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        conversation = conversation_service.create(
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            knowledge_base_id=request.knowledge_base_id,
        )

    # 保存用户消息
    conversation_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    # 获取对话历史
    history = conversation_service.get_recent_messages(
        conversation_id=conversation.id,
        limit=10,
    )
    history_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    # 生成响应
    response_text = ""
    thinking_text = ""
    async for chunk in agent_service.chat(
        message=request.message,
        knowledge_base_id=request.knowledge_base_id,
        conversation_history=history_dicts,
    ):
        if chunk.get("content"):
            response_text += chunk["content"]
        if chunk.get("thinking_content"):
            thinking_text += chunk["thinking_content"]

    # 获取引用
    results = retriever.retrieve(
        query=request.message,
        knowledge_base_id=str(request.knowledge_base_id) if request.knowledge_base_id else None,
    )
    references = agent_service.build_references(results)

    # 保存助手消息
    assistant_message = conversation_service.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        thinking_content=thinking_text if thinking_text else None,
        references={"items": references},
    )

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(assistant_message),
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: DBSession,
    retriever: RetrieverService,
    embedding: EmbeddingService,
) -> StreamingResponse:
    """
    流式对话

    Args:
        request: 对话请求
        db: 数据库会话
        retriever: 检索服务
        embedding: Embedding 服务

    Returns:
        流式响应
    """
    conversation_service = ConversationService(db)
    agent_service = AgentService(retriever, embedding)

    # 获取或创建对话
    if request.conversation_id:
        conversation = conversation_service.get_by_id(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        conversation = conversation_service.create(
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            knowledge_base_id=request.knowledge_base_id,
        )

    # 保存用户消息
    conversation_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    # 获取对话历史
    history = conversation_service.get_recent_messages(
        conversation_id=conversation.id,
        limit=10,
    )
    history_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    async def generate():
        response_text = ""
        thinking_text = ""
        async for chunk in agent_service.chat(
            message=request.message,
            knowledge_base_id=request.knowledge_base_id,
            conversation_history=history_dicts,
        ):
            if chunk.get("content"):
                response_text += chunk["content"]
            if chunk.get("thinking_content"):
                thinking_text += chunk["thinking_content"]

            # 返回 JSON 格式的数据
            yield json.dumps({
                "content": chunk.get("content", ""),
                "thinking_content": chunk.get("thinking_content", ""),
            }, ensure_ascii=False) + "\n"

        # 获取引用
        results = retriever.retrieve(
            query=request.message,
            knowledge_base_id=str(request.knowledge_base_id) if request.knowledge_base_id else None,
        )
        references = agent_service.build_references(results)

        # 保存助手消息
        conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            thinking_content=thinking_text if thinking_text else None,
            references={"items": references},
        )

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.get("/conversations", response_model=List[dict])
async def list_conversations(
    db: DBSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
) -> List[dict]:
    """
    列出对话

    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        search: 搜索关键词

    Returns:
        对话列表
    """
    service = ConversationService(db)
    items, total = service.list(page=page, page_size=page_size, search=search)

    return [
        {
            "id": item.id,
            "title": item.title,
            "knowledge_base_id": item.knowledge_base_id,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in items
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    db: DBSession,
    limit: int = Query(50, ge=1, le=200, description="消息数量"),
) -> List[MessageResponse]:
    """
    获取对话消息

    Args:
        conversation_id: 对话 ID
        db: 数据库会话
        limit: 消息数量

    Returns:
        消息列表
    """
    service = ConversationService(db)
    messages = service.get_messages(conversation_id=conversation_id, limit=limit)

    return [MessageResponse.model_validate(msg) for msg in messages]


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    db: DBSession,
) -> None:
    """
    删除对话

    Args:
        conversation_id: 对话 ID
        db: 数据库会话
    """
    service = ConversationService(db)
    success = service.delete(conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="对话不存在")
