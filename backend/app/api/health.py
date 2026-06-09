"""
健康检查 API

提供系统健康检查接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import DBSession, ESService

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    基本健康检查

    Returns:
        健康状态
    """
    return {"status": "ok", "service": "milo"}


@router.get("/health/detailed")
async def detailed_health_check(
    db: DBSession,
    es: ESService,
) -> dict:
    """
    详细健康检查

    Args:
        db: 数据库会话
        es: ES 客户端

    Returns:
        详细的健康状态
    """
    checks = {
        "status": "ok",
        "service": "milo",
        "components": {},
    }

    # 检查数据库
    try:
        db.execute("SELECT 1")
        checks["components"]["database"] = {"status": "ok"}
    except Exception as e:
        checks["components"]["database"] = {"status": "error", "message": str(e)}
        checks["status"] = "degraded"

    # 检查 Elasticsearch
    try:
        es_status = es.client.cluster.health()
        checks["components"]["elasticsearch"] = {
            "status": "ok",
            "cluster_status": es_status["status"],
        }
        if es_status["status"] != "green":
            checks["status"] = "degraded"
    except Exception as e:
        checks["components"]["elasticsearch"] = {"status": "error", "message": str(e)}
        checks["status"] = "degraded"

    return checks
