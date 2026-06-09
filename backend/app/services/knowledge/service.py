"""
知识库服务

提供知识库的 CRUD 操作。
"""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate


class KnowledgeBaseService:
    """知识库服务"""

    def __init__(self, db: Session) -> None:
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def create(self, data: KnowledgeBaseCreate) -> KnowledgeBase:
        """
        创建知识库

        Args:
            data: 创建数据

        Returns:
            创建的知识库
        """
        kb = KnowledgeBase(
            name=data.name,
            description=data.description,
            embedding_model=data.embedding_model,
        )
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def get_by_id(self, kb_id: int) -> Optional[KnowledgeBase]:
        """
        根据 ID 获取知识库

        Args:
            kb_id: 知识库 ID

        Returns:
            知识库或 None
        """
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    def get_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """
        根据名称获取知识库

        Args:
            name: 知识库名称

        Returns:
            知识库或 None
        """
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
    ) -> tuple[List[KnowledgeBase], int]:
        """
        列出知识库

        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词

        Returns:
            知识库列表和总数
        """
        query = self.db.query(KnowledgeBase)

        if search:
            query = query.filter(
                KnowledgeBase.name.contains(search) | KnowledgeBase.description.contains(search)
            )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def update(self, kb_id: int, data: KnowledgeBaseUpdate) -> Optional[KnowledgeBase]:
        """
        更新知识库

        Args:
            kb_id: 知识库 ID
            data: 更新数据

        Returns:
            更新后的知识库或 None
        """
        kb = self.get_by_id(kb_id)
        if not kb:
            return None

        if data.name is not None:
            kb.name = data.name
        if data.description is not None:
            kb.description = data.description
        if data.embedding_model is not None:
            kb.embedding_model = data.embedding_model

        self.db.commit()
        self.db.refresh(kb)
        return kb

    def delete(self, kb_id: int) -> bool:
        """
        删除知识库

        Args:
            kb_id: 知识库 ID

        Returns:
            是否删除成功
        """
        kb = self.get_by_id(kb_id)
        if not kb:
            return False

        self.db.delete(kb)
        self.db.commit()
        return True

    def get_stats(self, kb_id: int) -> Optional[dict]:
        """
        获取知识库统计信息

        Args:
            kb_id: 知识库 ID

        Returns:
            统计信息或 None
        """
        kb = self.get_by_id(kb_id)
        if not kb:
            return None

        document_count = (
            self.db.query(func.count(Document.id))
            .filter(Document.knowledge_base_id == kb_id)
            .scalar()
        )

        chunk_count = (
            self.db.query(func.sum(Document.chunk_count))
            .filter(Document.knowledge_base_id == kb_id)
            .scalar()
        ) or 0

        return {
            "document_count": document_count,
            "chunk_count": chunk_count,
        }
