"""
AgentScope 兼容的 Schedule API

Milo 暂不支持定时任务，返回空列表。
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def list_schedules():
    """列出定时任务（Milo 暂不支持）"""
    return {"schedules": [], "total": 0}


@router.post("/")
async def create_schedule():
    """创建定时任务（Milo 暂不支持）"""
    raise HTTPException(status_code=501, detail="Milo does not support scheduled tasks")


@router.patch("/{schedule_id}")
async def update_schedule(schedule_id: str):
    """更新定时任务（Milo 暂不支持）"""
    raise HTTPException(status_code=501, detail="Milo does not support scheduled tasks")


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str):
    """删除定时任务（Milo 暂不支持）"""
    raise HTTPException(status_code=501, detail="Milo does not support scheduled tasks")


@router.get("/{schedule_id}/sessions")
async def list_schedule_sessions(schedule_id: str):
    """列出定时任务的 Session（Milo 暂不支持）"""
    return {"sessions": [], "total": 0}
