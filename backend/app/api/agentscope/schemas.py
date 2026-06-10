"""
AgentScope 兼容的 Pydantic Schema 定义

与 AgentScope WebUI 前端期望的请求/响应格式完全匹配。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ========== 通用基础类型 ==========


class RecordBase(BaseModel):
    """所有记录的基类"""
    id: str
    created_at: str
    updated_at: str


class ChatModelConfig(BaseModel):
    """聊天模型配置"""
    type: str = "chat_model"
    credential_id: str = ""
    model: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ContextConfig(BaseModel):
    """Agent 上下文配置"""
    trigger_ratio: Optional[float] = None
    reserve_ratio: Optional[float] = None
    tool_result_limit: Optional[int] = None
    compression_prompt: Optional[str] = None
    summary_template: Optional[str] = None


class ReActConfig(BaseModel):
    """Agent ReAct 配置"""
    max_iters: Optional[int] = None
    stop_on_reject: Optional[bool] = None


# ========== Agent 类型 ==========


class AgentData(BaseModel):
    """Agent 数据"""
    id: str
    name: str
    system_prompt: str = ""
    context_config: ContextConfig = Field(default_factory=ContextConfig)
    react_config: ReActConfig = Field(default_factory=ReActConfig)


class AgentRecord(RecordBase):
    """Agent 完整记录"""
    user_id: str
    data: AgentData


class CreateAgentRequest(BaseModel):
    """创建 Agent 请求"""
    name: str
    system_prompt: Optional[str] = ""
    context_config: Optional[ContextConfig] = None
    react_config: Optional[ReActConfig] = None


class CreateAgentResponse(BaseModel):
    """创建 Agent 响应"""
    agent_id: str


class UpdateAgentRequest(BaseModel):
    """更新 Agent 请求"""
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    context_config: Optional[ContextConfig] = None
    react_config: Optional[ReActConfig] = None


class AgentListResponse(BaseModel):
    """Agent 列表响应"""
    agents: List[AgentRecord]
    total: int


# ========== Content Block 类型 ==========


class TextBlock(BaseModel):
    """文本块"""
    type: str = "text"
    id: str
    text: str


class ThinkingBlock(BaseModel):
    """思考块"""
    type: str = "thinking"
    id: str
    thinking: str


class HintBlock(BaseModel):
    """提示块"""
    type: str = "hint"
    id: str
    hint: Union[str, List[Any]]
    source: Optional[str] = None


class ContentBlock(BaseModel):
    """通用内容块"""
    type: str
    id: str
    # TextBlock fields
    text: Optional[str] = None
    # ThinkingBlock fields
    thinking: Optional[str] = None
    # HintBlock fields
    hint: Optional[Union[str, List[Any]]] = None
    source: Optional[str] = None

    class Config:
        extra = "allow"


# ========== Message 类型 ==========


class Msg(BaseModel):
    """消息"""
    id: str
    name: str
    role: str  # "user" | "assistant" | "system"
    content: List[ContentBlock] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    finished_at: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


# ========== Session 类型 ==========


class SessionConfig(BaseModel):
    """Session 配置"""
    name: str = "New Session"
    chat_model_config: ChatModelConfig = Field(default_factory=ChatModelConfig)
    fallback_chat_model_config: Optional[ChatModelConfig] = None
    workspace_id: str = ""


class SessionRecord(RecordBase):
    """Session 完整记录"""
    user_id: str
    agent_id: str
    source: str = "user"  # "user" | "schedule"
    source_schedule_id: Optional[str] = None
    team_id: Optional[str] = None
    config: SessionConfig = Field(default_factory=SessionConfig)
    state: Dict[str, Any] = Field(default_factory=dict)


class SessionView(BaseModel):
    """Session 视图（包含运行状态）"""
    session: SessionRecord
    is_running: bool = False
    team: Optional[Any] = None


class CreateSessionRequest(BaseModel):
    """创建 Session 请求"""
    agent_id: str
    workspace_id: Optional[str] = None
    chat_model_config: Optional[ChatModelConfig] = None
    fallback_chat_model_config: Optional[ChatModelConfig] = None


class CreateSessionResponse(BaseModel):
    """创建 Session 响应"""
    session_id: str


class UpdateSessionRequest(BaseModel):
    """更新 Session 请求"""
    name: Optional[str] = None
    chat_model_config: Optional[ChatModelConfig] = None
    fallback_chat_model_config: Optional[ChatModelConfig] = None
    permission_mode: Optional[str] = None


class SessionListResponse(BaseModel):
    """Session 列表响应"""
    sessions: List[SessionView]
    total: int


class MessagesResponse(BaseModel):
    """消息历史响应"""
    messages: List[Msg]
    is_running: bool = False


# ========== Chat 类型 ==========


class ChatInputMsg(BaseModel):
    """聊天输入消息"""
    id: str
    name: str
    role: str
    content: List[ContentBlock] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ChatRequest(BaseModel):
    """聊天请求"""
    agent_id: str
    session_id: str
    input: Optional[Union[ChatInputMsg, List[ChatInputMsg], Dict[str, Any], None]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    status: str = "ok"
    session_id: str


# ========== Credential 类型 ==========


class CredentialRecord(RecordBase):
    """凭证记录"""
    user_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class CreateCredentialRequest(BaseModel):
    """创建凭证请求"""
    data: Dict[str, Any]


class CreateCredentialResponse(BaseModel):
    """创建凭证响应"""
    credential_id: str


class UpdateCredentialRequest(BaseModel):
    """更新凭证请求"""
    data: Dict[str, Any]


class CredentialListResponse(BaseModel):
    """凭证列表响应"""
    credentials: List[CredentialRecord]
    total: int


class CredentialSchema(BaseModel):
    """凭证 Schema"""
    title: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: Optional[List[str]] = None


class CredentialSchemasResponse(BaseModel):
    """凭证 Schema 列表响应"""
    schemas: List[CredentialSchema]


# ========== Model 类型 ==========


class ModelCard(BaseModel):
    """模型卡片"""
    type: str = "chat_model"
    name: str
    label: str
    status: str = "active"  # "active" | "deprecated" | "sunset"
    deprecated_at: Optional[str] = None
    input_types: List[str] = Field(default_factory=lambda: ["text"])
    output_types: List[str] = Field(default_factory=lambda: ["text"])
    context_size: int = 131072
    output_size: int = 8192
    parameter_schema: Dict[str, Any] = Field(default_factory=dict)
    parameters_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ListModelResponse(BaseModel):
    """模型列表响应"""
    models: List[ModelCard]
    total: int


# ========== SSE Event 类型 ==========


class AgentEvent(BaseModel):
    """Agent 事件基类"""
    id: str
    created_at: str
    type: str

    class Config:
        extra = "allow"
