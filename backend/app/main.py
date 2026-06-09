"""
Milo 知识库 Agent FastAPI 应用工厂

提供应用创建、中间件配置、路由注册等功能。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, document, health, knowledge
from app.api.agentscope import (
    agent as as_agent,
    chat as as_chat,
    credential as as_credential,
    model as as_model,
    schedule as as_schedule,
    session as as_session,
    workspace as as_workspace,
)
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()
    yield
    # 关闭时执行


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    app = FastAPI(
        title=settings.APP_NAME,
        description="Milo 知识库 Agent API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
    app.include_router(document.router, prefix="/api/document", tags=["document"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

    # AgentScope 兼容 API（供 AgentScope WebUI 使用）
    app.include_router(as_agent.router, prefix="/agent", tags=["agentscope-agent"])
    app.include_router(as_session.router, prefix="/sessions", tags=["agentscope-session"])
    app.include_router(as_chat.router, prefix="/chat", tags=["agentscope-chat"])
    app.include_router(as_credential.router, prefix="/credential", tags=["agentscope-credential"])
    app.include_router(as_model.router, prefix="/model", tags=["agentscope-model"])
    app.include_router(as_workspace.router, prefix="/workspace", tags=["agentscope-workspace"])
    app.include_router(as_schedule.router, prefix="/schedule", tags=["agentscope-schedule"])

    return app


# 创建应用实例
app = create_app()
