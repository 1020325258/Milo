"""
知识库 API

提供知识库的 RESTful 接口。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import DBSession
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseList,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.knowledge.service import KnowledgeBaseService

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    db: DBSession,
) -> KnowledgeBaseResponse:
    """
    创建知识库

    Args:
        data: 创建数据
        db: 数据库会话

    Returns:
        创建的知识库
    """
    service = KnowledgeBaseService(db)

    # 检查名称是否已存在
    existing = service.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="知识库名称已存在")

    kb = service.create(data)
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/", response_model=KnowledgeBaseList)
async def list_knowledge_bases(
    db: DBSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
) -> KnowledgeBaseList:
    """
    列出知识库

    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        search: 搜索关键词

    Returns:
        知识库列表
    """
    service = KnowledgeBaseService(db)
    items, total = service.list(page=page, page_size=page_size, search=search)

    # 包含统计数据
    response_items = []
    for item in items:
        stats = service.get_stats(item.id)
        data = KnowledgeBaseResponse.model_validate(item)
        if stats:
            data.document_count = stats.get("document_count", 0)
            data.chunk_count = stats.get("chunk_count", 0)
        response_items.append(data)

    return KnowledgeBaseList(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    db: DBSession,
) -> KnowledgeBaseResponse:
    """
    获取知识库详情

    Args:
        kb_id: 知识库 ID
        db: 数据库会话

    Returns:
        知识库详情
    """
    service = KnowledgeBaseService(db)
    kb = service.get_by_id(kb_id)

    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    return KnowledgeBaseResponse.model_validate(kb)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    data: KnowledgeBaseUpdate,
    db: DBSession,
) -> KnowledgeBaseResponse:
    """
    更新知识库

    Args:
        kb_id: 知识库 ID
        data: 更新数据
        db: 数据库会话

    Returns:
        更新后的知识库
    """
    service = KnowledgeBaseService(db)

    # 检查名称是否已存在
    if data.name:
        existing = service.get_by_name(data.name)
        if existing and existing.id != kb_id:
            raise HTTPException(status_code=400, detail="知识库名称已存在")

    kb = service.update(kb_id, data)

    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    return KnowledgeBaseResponse.model_validate(kb)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: int,
    db: DBSession,
) -> None:
    """
    删除知识库

    Args:
        kb_id: 知识库 ID
        db: 数据库会话
    """
    service = KnowledgeBaseService(db)
    success = service.delete(kb_id)

    if not success:
        raise HTTPException(status_code=404, detail="知识库不存在")


@router.get("/{kb_id}/stats")
async def get_knowledge_base_stats(
    kb_id: int,
    db: DBSession,
) -> dict:
    """
    获取知识库统计信息

    Args:
        kb_id: 知识库 ID
        db: 数据库会话

    Returns:
        统计信息
    """
    service = KnowledgeBaseService(db)
    stats = service.get_stats(kb_id)

    if not stats:
        raise HTTPException(status_code=404, detail="知识库不存在")

    return stats
