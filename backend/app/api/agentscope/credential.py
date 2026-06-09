"""
AgentScope 兼容的 Credential API

Milo 使用环境变量配置 DashScope API Key，
此路由提供只读的凭证信息。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.agentscope.schemas import (
    CreateCredentialRequest,
    CreateCredentialResponse,
    CredentialListResponse,
    CredentialRecord,
    CredentialSchema,
    CredentialSchemasResponse,
    UpdateCredentialRequest,
)
from app.core.config import settings

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# 内置 DashScope 凭证
_DASHSCOPE_CREDENTIAL_ID = "dashscope-default"


def _get_dashscope_record() -> CredentialRecord:
    return CredentialRecord(
        id=_DASHSCOPE_CREDENTIAL_ID,
        created_at=_now_iso(),
        updated_at=_now_iso(),
        user_id="system",
        data={
            "type": "dashscope",
            "provider": "dashscope",
            "api_key": settings.DASHSCOPE_API_KEY[:8] + "***" if settings.DASHSCOPE_API_KEY else "",
        },
    )


@router.get("/", response_model=CredentialListResponse)
async def list_credentials():
    """列出凭证"""
    records = [_get_dashscope_record()]
    return CredentialListResponse(credentials=records, total=len(records))


@router.get("/schemas", response_model=CredentialSchemasResponse)
async def get_credential_schemas():
    """获取凭证 Schema"""
    return CredentialSchemasResponse(schemas=[
        CredentialSchema(
            title="DashScope",
            type="dashscope",
            properties={
                "api_key": {"type": "string", "description": "DashScope API Key", "writeOnly": True},
            },
            required=["api_key"],
        ),
    ])


@router.post("/", response_model=CreateCredentialResponse)
async def create_credential(request: CreateCredentialRequest):
    """创建凭证（Milo 中为 stub）"""
    import uuid
    return CreateCredentialResponse(credential_id=str(uuid.uuid4()))


@router.patch("/{credential_id}", response_model=CredentialRecord)
async def update_credential(credential_id: str, request: UpdateCredentialRequest):
    """更新凭证（Milo 中为 stub）"""
    raise HTTPException(status_code=501, detail="Milo manages credentials via environment variables")


@router.delete("/{credential_id}", status_code=204)
async def delete_credential(credential_id: str):
    """删除凭证（Milo 中为 stub）"""
    raise HTTPException(status_code=501, detail="Milo manages credentials via environment variables")
