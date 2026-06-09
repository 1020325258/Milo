"""
AgentScope 兼容的 Chat API

POST /chat/ — 触发聊天（fire-and-forget）
GET /sessions/{sessionId}/stream — SSE 事件流
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession

from app.api.agentscope.event_emitter import (
    event_emitter,
    format_sse,
    make_heartbeat,
    make_hint_block,
    make_model_call_end,
    make_model_call_start,
    make_reply_end,
    make_reply_start,
    make_text_block_delta,
    make_text_block_end,
    make_text_block_start,
    make_thinking_block_delta,
    make_thinking_block_end,
    make_thinking_block_start,
)
from app.api.agentscope.schemas import ChatRequest, ChatResponse
from app.api.agentscope.session import (
    _milo_message_to_msg,
    is_session_running,
    set_session_running,
)
from app.core.deps import DBSession as DBSessionDep
from app.core.deps import EmbeddingService, RetrieverService
from app.services.agent.service import AgentService
from app.services.conversation.service import ConversationService

router = APIRouter()


async def _run_rag_pipeline(
    session_id: str,
    user_message: str,
    knowledge_base_id: Optional[int],
    db_url: str,
):
    """
    后台运行 RAG 流程，将输出转换为 SSE 事件发布到事件总线。

    这个函数在后台 task 中运行，通过 event_emitter 将事件推送给 SSE 流。
    """
    from app.core.database import SessionLocal
    from app.core.elasticsearch import get_es_client
    from app.services.embedding.dashscope import DashScopeEmbeddingService
    from app.services.retrieval.reranker import DashScopeReranker
    from app.services.retrieval.retriever import Retriever

    reply_id = uuid.uuid4().hex
    thinking_block_id = f"thinking-{uuid.uuid4().hex[:8]}"
    text_block_id = f"text-{uuid.uuid4().hex[:8]}"

    set_session_running(session_id, True)
    thinking_started = False
    text_started = False

    try:
        # 发送 REPLY_START
        await event_emitter.emit_event(
            session_id,
            make_reply_start(session_id, reply_id),
        )

        # 创建独立的数据库会话
        db = SessionLocal()
        try:
            conversation_service = ConversationService(db)

            # 获取对话历史
            history = conversation_service.get_recent_messages(
                conversation_id=int(session_id),
                limit=10,
            )
            history_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history)
            ]

            # 初始化检索服务
            from app.core.config import settings
            from app.core.elasticsearch import get_es_client

            embedding_service = DashScopeEmbeddingService()
            reranker = DashScopeReranker()
            retriever = Retriever(get_es_client(), embedding_service, reranker)
            agent_service = AgentService(retriever, embedding_service)

            # 发送 MODEL_CALL_START
            from app.core.config import settings
            await event_emitter.emit_event(
                session_id,
                make_model_call_start(reply_id, settings.LLM_MODEL),
            )

            # 跟踪响应内容
            response_text = ""
            thinking_text = ""

            # 查询文档名称映射
            doc_names = {}
            if knowledge_base_id:
                from app.models.document import Document
                docs = db.query(Document).filter(
                    Document.knowledge_base_id == knowledge_base_id
                ).all()
                doc_names = {str(doc.id): doc.filename for doc in docs}

            # 运行 RAG 流程
            async for chunk in agent_service.chat(
                message=user_message,
                knowledge_base_id=knowledge_base_id,
                conversation_history=history_dicts,
                doc_names=doc_names,
            ):
                # 处理 thinking_content
                if chunk.get("thinking_content"):
                    if not thinking_started:
                        await event_emitter.emit_event(
                            session_id,
                            make_thinking_block_start(reply_id, thinking_block_id),
                        )
                        thinking_started = True
                    thinking_text += chunk["thinking_content"]
                    await event_emitter.emit_event(
                        session_id,
                        make_thinking_block_delta(reply_id, thinking_block_id, chunk["thinking_content"]),
                    )

                # 处理 content
                if chunk.get("content"):
                    if not text_started:
                        # 如果有 thinking，先结束 thinking block
                        if thinking_started:
                            await event_emitter.emit_event(
                                session_id,
                                make_thinking_block_end(reply_id, thinking_block_id),
                            )
                            thinking_started = False
                        await event_emitter.emit_event(
                            session_id,
                            make_text_block_start(reply_id, text_block_id),
                        )
                        text_started = True
                    response_text += chunk["content"]
                    await event_emitter.emit_event(
                        session_id,
                        make_text_block_delta(reply_id, text_block_id, chunk["content"]),
                    )

            # 结束未关闭的 block
            if thinking_started:
                await event_emitter.emit_event(
                    session_id,
                    make_thinking_block_end(reply_id, thinking_block_id),
                )
            if text_started:
                await event_emitter.emit_event(
                    session_id,
                    make_text_block_end(reply_id, text_block_id),
                )

            # 发送引用信息
            results = retriever.retrieve(
                query=user_message,
                knowledge_base_id=str(knowledge_base_id) if knowledge_base_id else None,
            )

            # 查询文档名称
            doc_names = {}
            if results:
                doc_ids = list(set(r.document_id for r in results if r.document_id))
                if doc_ids:
                    from app.models.document import Document
                    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
                    doc_names = {str(doc.id): doc.filename for doc in docs}

            references = agent_service.build_references(results, doc_names=doc_names)

            if references:
                ref_data = []
                for ref in references:
                    ref_data.append({
                        "index": ref.get("index", ""),
                        "name": ref.get("document_name", f"文档 {ref.get('document_id', '')}"),
                        "doc_id": ref.get("document_id", ""),
                    })
                hint_text = json.dumps({"references": ref_data}, ensure_ascii=False)
                await event_emitter.emit_event(
                    session_id,
                    make_hint_block(reply_id, f"hint-{uuid.uuid4().hex[:8]}", hint_text, "milo-retrieval"),
                )

            # 发送 MODEL_CALL_END
            await event_emitter.emit_event(
                session_id,
                make_model_call_end(reply_id),
            )

            # 保存助手消息到数据库
            conversation_service.add_message(
                conversation_id=int(session_id),
                role="assistant",
                content=response_text,
                thinking_content=thinking_text if thinking_text else None,
                references={"items": references} if references else None,
            )

        finally:
            db.close()

    except Exception as e:
        # 发送错误信息
        error_text = f"抱歉，处理您的请求时出现错误：{str(e)}"
        if not text_started:
            await event_emitter.emit_event(
                session_id,
                make_text_block_start(reply_id, text_block_id),
            )
        await event_emitter.emit_event(
            session_id,
            make_text_block_delta(reply_id, text_block_id, error_text),
        )
        await event_emitter.emit_event(
            session_id,
            make_text_block_end(reply_id, text_block_id),
        )

    finally:
        # 发送 REPLY_END
        await event_emitter.emit_event(
            session_id,
            make_reply_end(session_id, reply_id),
        )
        set_session_running(session_id, False)


@router.post("/", response_model=ChatResponse)
async def trigger_chat(
    request: ChatRequest,
    db: DBSessionDep,
):
    """
    触发聊天（fire-and-forget）

    接收用户消息，启动后台 RAG 流程，立即返回。
    实际的响应通过 SSE 流推送。
    """
    session_id = request.session_id

    # 验证 session 存在
    conversation_service = ConversationService(db)
    conv = conversation_service.get_by_id(int(session_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    # 提取用户消息
    user_message = ""
    if request.input:
        if isinstance(request.input, dict):
            # 可能是 Msg 对象
            content = request.input.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        user_message += block.get("text", "")
            elif isinstance(content, str):
                user_message = content
        elif hasattr(request.input, "content"):
            # ChatInputMsg 对象
            for block in request.input.content:
                if block.type == "text" and block.text:
                    user_message += block.text

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # 保存用户消息
    conversation_service.add_message(
        conversation_id=int(session_id),
        role="user",
        content=user_message,
    )

    # 获取知识库 ID
    knowledge_base_id = conv.knowledge_base_id

    # 确保事件总线已创建（RAG pipeline 发布事件时需要）
    event_emitter.get_or_create_bus(session_id)

    # 启动后台 RAG 任务
    from app.core.config import settings
    asyncio.create_task(
        _run_rag_pipeline(
            session_id=session_id,
            user_message=user_message,
            knowledge_base_id=knowledge_base_id,
            db_url=settings.DATABASE_URL,
        )
    )

    return ChatResponse(status="ok", session_id=session_id)


# 注意：SSE 流端点已移至 session.py（GET /sessions/{session_id}/stream）
