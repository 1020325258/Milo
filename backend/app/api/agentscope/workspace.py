"""
AgentScope 兼容的 Workspace API

Milo 暂不支持 MCP 和 Skill 管理，返回空列表。
"""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/mcp")
async def list_mcp(
    agent_id: str = Query(...),
    session_id: str = Query(...),
):
    """列出 MCP 服务（Milo 暂不支持）"""
    return []


@router.post("/mcp", status_code=204)
async def add_mcp(
    agent_id: str = Query(...),
    session_id: str = Query(...),
):
    """添加 MCP 服务（Milo 暂不支持）"""
    pass


@router.delete("/mcp/{mcp_name}", status_code=204)
async def remove_mcp(
    mcp_name: str,
    agent_id: str = Query(...),
    session_id: str = Query(...),
):
    """移除 MCP 服务（Milo 暂不支持）"""
    pass


@router.get("/skill")
async def list_skills(
    agent_id: str = Query(...),
    session_id: str = Query(...),
):
    """列出 Skill（Milo 暂不支持）"""
    return []


@router.post("/skill", status_code=204)
async def add_skill(
    agent_id: str = Query(...),
    session_id: str = Query(...),
):
    """添加 Skill（Milo 暂不支持）"""
    pass


@router.delete("/skill/{skill_name}", status_code=204)
async def remove_skill(
    skill_name: str,
    agent_id: str = Query(...),
    session_id: str = Query(...),
):
    """移除 Skill（Milo 暂不支持）"""
    pass
