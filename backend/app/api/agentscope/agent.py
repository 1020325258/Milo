"""
AgentScope 兼容的 Agent API

Milo 内置一个默认 Agent（"Milo Knowledge Agent"），代表 RAG 知识库助手。
支持创建/更新/删除自定义 Agent。
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

from app.api.agentscope.schemas import (
    AgentData,
    AgentListResponse,
    AgentRecord,
    ContextConfig,
    CreateAgentRequest,
    CreateAgentResponse,
    ReActConfig,
    UpdateAgentRequest,
)

router = APIRouter()

# 内存中的 Agent 存储（生产环境可持久化到数据库）
_agents: Dict[str, AgentRecord] = {}

# 内置默认 Agent
_DEFAULT_AGENT_ID = "milo-knowledge-agent"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_default_agent():
    """确保默认 Agent 存在"""
    if _DEFAULT_AGENT_ID not in _agents:
        now = _now_iso()
        _agents[_DEFAULT_AGENT_ID] = AgentRecord(
            id=_DEFAULT_AGENT_ID,
            created_at=now,
            updated_at=now,
            user_id="system",
            data=AgentData(
                id=_DEFAULT_AGENT_ID,
                name="Milo Knowledge Agent",
                system_prompt="你是一个知识库助手，基于检索到的文档内容回答用户问题。请用中文回答。",
                context_config=ContextConfig(),
                react_config=ReActConfig(),
            ),
        )


@router.get("/", response_model=AgentListResponse)
async def list_agents():
    """列出所有 Agent"""
    _ensure_default_agent()
    agents = list(_agents.values())
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/schema")
async def get_agent_schema():
    """获取 Agent 配置 Schema"""
    return {
        "identity": {
            "title": "Agent Identity",
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent 名称"},
                "system_prompt": {"type": "string", "description": "系统提示词"},
            },
        },
        "context_config": {
            "title": "Context Config",
            "type": "object",
            "properties": {
                "trigger_ratio": {"type": "number", "description": "触发比率"},
                "reserve_ratio": {"type": "number", "description": "保留比率"},
                "tool_result_limit": {"type": "integer", "description": "工具结果限制"},
            },
        },
        "react_config": {
            "title": "ReAct Config",
            "type": "object",
            "properties": {
                "max_iters": {"type": "integer", "description": "最大迭代次数"},
                "stop_on_reject": {"type": "boolean", "description": "拒绝时停止"},
            },
        },
    }


@router.post("/", response_model=CreateAgentResponse)
async def create_agent(request: CreateAgentRequest):
    """创建 Agent"""
    _ensure_default_agent()
    agent_id = str(uuid.uuid4())
    now = _now_iso()

    record = AgentRecord(
        id=agent_id,
        created_at=now,
        updated_at=now,
        user_id="default",
        data=AgentData(
            id=agent_id,
            name=request.name,
            system_prompt=request.system_prompt or "",
            context_config=request.context_config or ContextConfig(),
            react_config=request.react_config or ReActConfig(),
        ),
    )
    _agents[agent_id] = record
    return CreateAgentResponse(agent_id=agent_id)


@router.patch("/{agent_id}", response_model=AgentRecord)
async def update_agent(agent_id: str, request: UpdateAgentRequest):
    """更新 Agent"""
    _ensure_default_agent()
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    record = _agents[agent_id]
    data = record.data

    if request.name is not None:
        data.name = request.name
    if request.system_prompt is not None:
        data.system_prompt = request.system_prompt
    if request.context_config is not None:
        data.context_config = request.context_config
    if request.react_config is not None:
        data.react_config = request.react_config

    record.updated_at = _now_iso()
    _agents[agent_id] = record
    return record


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    """删除 Agent"""
    if agent_id == _DEFAULT_AGENT_ID:
        raise HTTPException(status_code=400, detail="Cannot delete the default agent")
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    del _agents[agent_id]
