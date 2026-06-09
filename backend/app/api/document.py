"""
文档 API

提供文档的 RESTful 接口。
"""

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.deps import DBSession, ESService, EmbeddingService
from app.schemas.document import DocumentList, DocumentResponse
from app.services.document.service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
    file: UploadFile = File(...),
    knowledge_base_id: int = Form(...),
) -> DocumentResponse:
    """
    上传文档

    Args:
        db: 数据库会话
        es: ES 客户端
        embedding: Embedding 服务
        file: 上传的文件
        knowledge_base_id: 知识库 ID

    Returns:
        创建的文档
    """
    service = DocumentService(db, es, embedding)

    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in service.parsers:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        content = await file.read()
        temp.write(content)
        temp_path = temp.name

    try:
        doc = service.upload(
            file_path=temp_path,
            filename=file.filename,
            knowledge_base_id=knowledge_base_id,
        )
        return DocumentResponse.model_validate(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/{doc_id}/process", response_model=DocumentResponse)
async def process_document(
    doc_id: int,
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
) -> DocumentResponse:
    """
    处理文档

    Args:
        doc_id: 文档 ID
        db: 数据库会话
        es: ES 客户端
        embedding: Embedding 服务

    Returns:
        更新后的文档
    """
    service = DocumentService(db, es, embedding)

    try:
        service.process(doc_id)
        doc = service.get_by_id(doc_id)

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        return DocumentResponse.model_validate(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/", response_model=DocumentList)
async def list_documents(
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
    knowledge_base_id: int = Query(..., description="知识库 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> DocumentList:
    """
    列出文档

    Args:
        db: 数据库会话
        es: ES 客户端
        embedding: Embedding 服务
        knowledge_base_id: 知识库 ID
        page: 页码
        page_size: 每页数量

    Returns:
        文档列表
    """
    service = DocumentService(db, es, embedding)
    items, total = service.list_by_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
    )

    return DocumentList(
        items=[DocumentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
) -> DocumentResponse:
    """
    获取文档详情

    Args:
        doc_id: 文档 ID
        db: 数据库会话
        es: ES 客户端
        embedding: Embedding 服务

    Returns:
        文档详情
    """
    service = DocumentService(db, es, embedding)
    doc = service.get_by_id(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return DocumentResponse.model_validate(doc)


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
):
    """
    下载文档文件

    Args:
        doc_id: 文档 ID

    Returns:
        文件内容
    """
    from fastapi.responses import FileResponse

    service = DocumentService(db, es, embedding)
    doc = service.get_by_id(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type="application/octet-stream",
    )


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: int,
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
):
    """
    获取文档内容（在线查看）

    Args:
        doc_id: 文档 ID

    Returns:
        文档文本内容
    """
    from fastapi.responses import PlainTextResponse

    service = DocumentService(db, es, embedding)
    doc = service.get_by_id(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        with open(doc.file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # PDF 等二进制文件，返回提示
        return PlainTextResponse(
            f"文件类型 '{doc.file_type}' 不支持在线预览，请下载查看。",
            status_code=200,
        )

    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")


@router.get("/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: int,
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
):
    """
    获取文档的所有分片

    Args:
        doc_id: 文档 ID

    Returns:
        分片列表
    """
    service = DocumentService(db, es, embedding)
    doc = service.get_by_id(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    from app.models.chunk import Chunk
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.chunk_index).all()

    return {
        "document_id": doc_id,
        "filename": doc.filename,
        "total": len(chunks),
        "chunks": [
            {
                "id": c.id,
                "chunk_id": c.chunk_id,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "section_title": c.section_title,
                "start_offset": c.start_offset,
                "end_offset": c.end_offset,
            }
            for c in chunks
        ],
    }


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: DBSession,
    es: ESService,
    embedding: EmbeddingService,
) -> None:
    """
    删除文档

    Args:
        doc_id: 文档 ID
        db: 数据库会话
        es: ES 客户端
        embedding: Embedding 服务
    """
    service = DocumentService(db, es, embedding)
    success = service.delete(doc_id)

    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
