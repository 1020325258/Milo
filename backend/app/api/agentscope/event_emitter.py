"""
SSE 事件发射器

将 Milo 的 RAG 流式输出转换为 AgentScope 的 SSE 事件格式。
使用发布-订阅模式：RAG pipeline 发布事件，多个 SSE 连接各自接收。
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_id() -> str:
    return uuid.uuid4().hex


class SessionEventBus:
    """单个 Session 的事件总线（支持多订阅者）"""

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []
        self._history: List[Dict[str, Any]] = []  # 保存事件历史，供迟到的订阅者回放

    async def publish(self, event: Dict[str, Any]):
        """发布事件到所有订阅者，并保存到历史"""
        self._history.append(event)
        for queue in self._subscribers:
            await queue.put(event)

    def subscribe(self) -> asyncio.Queue:
        """订阅事件流，返回一个 Queue"""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """取消订阅"""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


class EventEmitter:
    """全局事件发射器，管理所有 Session 的事件总线"""

    def __init__(self):
        self._buses: Dict[str, SessionEventBus] = {}

    def get_or_create_bus(self, session_id: str) -> SessionEventBus:
        """获取或创建 Session 的事件总线"""
        if session_id not in self._buses:
            self._buses[session_id] = SessionEventBus()
        return self._buses[session_id]

    def get_bus(self, session_id: str) -> Optional[SessionEventBus]:
        """获取 Session 的事件总线"""
        return self._buses.get(session_id)

    def remove_bus(self, session_id: str):
        """移除 Session 的事件总线"""
        self._buses.pop(session_id, None)

    async def emit_event(self, session_id: str, event: Dict[str, Any]):
        """向指定 Session 发射事件（自动创建 bus）"""
        bus = self.get_or_create_bus(session_id)
        await bus.publish(event)

    async def subscribe(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅指定 Session 的事件流"""
        bus = self.get_or_create_bus(session_id)
        queue = bus.subscribe()
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        finally:
            bus.unsubscribe(queue)


# 全局单例
event_emitter = EventEmitter()


def make_event(event_type: str, **kwargs) -> Dict[str, Any]:
    """创建事件对象"""
    event = {
        "id": _new_id(),
        "created_at": _now_iso(),
        "type": event_type,
        **kwargs,
    }
    return event


def make_reply_start(session_id: str, reply_id: str, name: str = "Milo") -> Dict[str, Any]:
    return make_event(
        "REPLY_START",
        session_id=session_id,
        reply_id=reply_id,
        name=name,
        role="assistant",
    )


def make_reply_end(session_id: str, reply_id: str) -> Dict[str, Any]:
    return make_event(
        "REPLY_END",
        session_id=session_id,
        reply_id=reply_id,
    )


def make_model_call_start(reply_id: str, model_name: str) -> Dict[str, Any]:
    return make_event(
        "MODEL_CALL_START",
        reply_id=reply_id,
        model_name=model_name,
    )


def make_model_call_end(reply_id: str, input_tokens: int = 0, output_tokens: int = 0) -> Dict[str, Any]:
    return make_event(
        "MODEL_CALL_END",
        reply_id=reply_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def make_thinking_block_start(reply_id: str, block_id: str) -> Dict[str, Any]:
    return make_event(
        "THINKING_BLOCK_START",
        reply_id=reply_id,
        block_id=block_id,
    )


def make_thinking_block_delta(reply_id: str, block_id: str, delta: str) -> Dict[str, Any]:
    return make_event(
        "THINKING_BLOCK_DELTA",
        reply_id=reply_id,
        block_id=block_id,
        delta=delta,
    )


def make_thinking_block_end(reply_id: str, block_id: str) -> Dict[str, Any]:
    return make_event(
        "THINKING_BLOCK_END",
        reply_id=reply_id,
        block_id=block_id,
    )


def make_text_block_start(reply_id: str, block_id: str) -> Dict[str, Any]:
    return make_event(
        "TEXT_BLOCK_START",
        reply_id=reply_id,
        block_id=block_id,
    )


def make_text_block_delta(reply_id: str, block_id: str, delta: str) -> Dict[str, Any]:
    return make_event(
        "TEXT_BLOCK_DELTA",
        reply_id=reply_id,
        block_id=block_id,
        delta=delta,
    )


def make_text_block_end(reply_id: str, block_id: str) -> Dict[str, Any]:
    return make_event(
        "TEXT_BLOCK_END",
        reply_id=reply_id,
        block_id=block_id,
    )


def make_hint_block(reply_id: str, block_id: str, hint: str, source: str = "milo-retrieval") -> Dict[str, Any]:
    return make_event(
        "HINT_BLOCK",
        reply_id=reply_id,
        block_id=block_id,
        hint=hint,
        source=source,
    )


def format_sse(event: Dict[str, Any]) -> str:
    """将事件格式化为 SSE 文本"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def make_heartbeat() -> str:
    """创建心跳消息"""
    return ": heartbeat\n\n"
