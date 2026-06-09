"""
AgentScope 兼容的 Session API

Session 映射到 Milo 的 Conversation（会话）模型。
消息历史转换为 AgentScope 的 Msg 格式返回。
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession

from app.api.agentscope.schemas import (
    ChatModelConfig,
    ContentBlock,
    CreateSessionRequest,
    CreateSessionResponse,
    MessagesResponse,
    Msg,
    SessionConfig,
    SessionListResponse,
    SessionRecord,
    SessionView,
    UpdateSessionRequest,
)
from app.core.database import get_db
from app.services.conversation.service import ConversationService

router = APIRouter()

# 运行中的 session 状态跟踪
_running_sessions: set = set()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _conversation_to_session_record(conv, agent_id: str = "milo-knowledge-agent") -> SessionRecord:
    """将 Milo Conversation 转换为 AgentScope SessionRecord"""
    return SessionRecord(
        id=str(conv.id),
        created_at=conv.created_at.isoformat() + "Z" if conv.created_at else _now_iso(),
        updated_at=conv.updated_at.isoformat() + "Z" if conv.updated_at else _now_iso(),
        user_id="default",
        agent_id=agent_id,
        source="user",
        source_schedule_id=None,
        team_id=None,
        config=SessionConfig(
            name=conv.title or "New Session",
            chat_model_config=ChatModelConfig(),
            fallback_chat_model_config=None,
            workspace_id="",
        ),
        state={},
    )


def _milo_message_to_msg(msg) -> Msg:
    """将 Milo Message 转换为 AgentScope Msg 格式"""
    content_blocks = []

    # 思考内容作为 ThinkingBlock
    if msg.thinking_content:
        content_blocks.append(ContentBlock(
            type="thinking",
            id=f"thinking-{msg.id}",
            thinking=msg.thinking_content,
        ))

    # 主要内容作为 TextBlock
    content_blocks.append(ContentBlock(
        type="text",
        id=f"text-{msg.id}",
        text=msg.content or "",
    ))

    # 引用作为 HintBlock
    if msg.references and isinstance(msg.references, dict):
        items = msg.references.get("items", [])
        if items:
            hint_lines = []
            for ref in items:
                idx = ref.get("index", "")
                doc_name = ref.get("document_name", ref.get("document_id", ""))
                hint_lines.append(f"[{idx}] {doc_name}")
            content_blocks.append(ContentBlock(
                type="hint",
                id=f"hint-{msg.id}",
                hint="参考文档：\n" + "\n".join(hint_lines),
                source="milo-retrieval",
            ))

    # 确定 name
    name = "Milo" if msg.role == "assistant" else "User"

    return Msg(
        id=str(msg.id),
        name=name,
        role=msg.role,
        content=content_blocks,
        metadata={},
        created_at=msg.created_at.isoformat() + "Z" if msg.created_at else _now_iso(),
        finished_at=msg.updated_at.isoformat() + "Z" if msg.role == "assistant" and msg.updated_at else None,
    )


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    agent_id: str = Query(..., description="Agent ID"),
    db: DBSession = Depends(get_db),
):
    """列出指定 Agent 的所有 Session"""
    service = ConversationService(db)
    items, total = service.list(page=1, page_size=1000)

    sessions = []
    for conv in items:
        record = _conversation_to_session_record(conv, agent_id)
        is_running = str(conv.id) in _running_sessions
        sessions.append(SessionView(
            session=record,
            is_running=is_running,
            team=None,
        ))

    return SessionListResponse(sessions=sessions, total=total)


@router.post("/", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: DBSession = Depends(get_db),
):
    """创建新 Session（对应创建新的 Conversation）"""
    service = ConversationService(db)
    conv = service.create(
        title="New Session",
        knowledge_base_id=None,
    )
    return CreateSessionResponse(session_id=str(conv.id))


@router.patch("/{session_id}", response_model=SessionRecord)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    agent_id: str = Query(..., description="Agent ID"),
    db: DBSession = Depends(get_db),
):
    """更新 Session"""
    service = ConversationService(db)
    conv = service.get_by_id(int(session_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.name:
        service.update_title(int(session_id), request.name)

    # 重新获取更新后的数据
    conv = service.get_by_id(int(session_id))
    return _conversation_to_session_record(conv, agent_id)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    agent_id: str = Query(..., description="Agent ID"),
    db: DBSession = Depends(get_db),
):
    """删除 Session"""
    service = ConversationService(db)
    success = service.delete(int(session_id))
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/messages", response_model=MessagesResponse)
async def get_messages(
    session_id: str,
    agent_id: str = Query(..., description="Agent ID"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: DBSession = Depends(get_db),
):
    """获取 Session 的消息历史"""
    service = ConversationService(db)
    conv = service.get_by_id(int(session_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = service.get_messages(int(session_id), limit=limit)
    msgs = [_milo_message_to_msg(m) for m in messages]

    is_running = session_id in _running_sessions
    return MessagesResponse(messages=msgs, is_running=is_running)


@router.get("/{session_id}/stream")
async def stream_events(
    session_id: str,
    agent_id: str = Query("milo-knowledge-agent"),
):
    """
    SSE 事件流

    长连接，持续推送指定 Session 的 Agent 事件。
    前端通过此端点接收 RAG 流程的实时输出。
    """
    from app.api.agentscope.event_emitter import event_emitter, format_sse

    async def event_generator():
        # 发送初始连接确认
        yield format_sse({
            "id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "type": "CUSTOM",
            "name": "connected",
            "value": {"session_id": session_id},
        })

        # 订阅事件流
        try:
            async for event in event_emitter.subscribe(session_id):
                yield format_sse(event)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def set_session_running(session_id: str, running: bool):
    """设置 session 运行状态"""
    if running:
        _running_sessions.add(session_id)
    else:
        _running_sessions.discard(session_id)


def is_session_running(session_id: str) -> bool:
    """检查 session 是否正在运行"""
    return session_id in _running_sessions
