"""
AgentScope 兼容的 Model API

返回 Milo 支持的模型列表（DashScope Qwen 系列）。
"""

from fastapi import APIRouter, Query

from app.api.agentscope.schemas import ListModelResponse, ModelCard

router = APIRouter()

# Milo 支持的模型列表
_MODELS = [
    ModelCard(
        type="chat_model",
        name="qwen-max",
        label="Qwen Max",
        status="active",
        input_types=["text"],
        output_types=["text"],
        context_size=131072,
        output_size=8192,
        parameter_schema={
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 8192, "default": 2000},
        },
    ),
    ModelCard(
        type="chat_model",
        name="qwen-plus",
        label="Qwen Plus",
        status="active",
        input_types=["text"],
        output_types=["text"],
        context_size=131072,
        output_size=8192,
        parameter_schema={
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 8192, "default": 2000},
        },
    ),
    ModelCard(
        type="chat_model",
        name="qwen-turbo",
        label="Qwen Turbo",
        status="active",
        input_types=["text"],
        output_types=["text"],
        context_size=131072,
        output_size=8192,
        parameter_schema={
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 8192, "default": 2000},
        },
    ),
    ModelCard(
        type="chat_model",
        name="qwen-long",
        label="Qwen Long",
        status="active",
        input_types=["text"],
        output_types=["text"],
        context_size=10000000,
        output_size=8192,
        parameter_schema={
            "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 8192, "default": 2000},
        },
    ),
]


@router.get("/", response_model=ListModelResponse)
async def list_models(provider: str = Query(..., description="模型提供商")):
    """列出指定提供商的模型"""
    if provider == "dashscope":
        return ListModelResponse(models=_MODELS, total=len(_MODELS))
    return ListModelResponse(models=[], total=0)
