"""
文档服务

提供文档的上传、处理、删除等功能。
"""

import os
import shutil
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.services.chunking.smart_chunker import SmartChunker
from app.services.document.md_parser import MarkdownParser
from app.services.document.parser import BaseParser, ParsedDocument
from app.services.document.pdf_parser import PDFParser
from app.services.embedding.base import BaseEmbeddingService
from app.services.retrieval.es_client import ESClient


class DocumentService:
    """文档服务"""

    # 使用绝对路径，避免 CWD 影响
    # __file__ = .../backend/app/services/document/service.py
    # 需要回溯 4 层到 backend/
    _BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    UPLOAD_DIR = os.path.join(_BACKEND_DIR, "uploads")

    def __init__(
        self,
        db: Session,
        es: ESClient,
        embedding: BaseEmbeddingService,
    ) -> None:
        """
        初始化服务

        Args:
            db: 数据库会话
            es: ES 客户端
            embedding: Embedding 服务
        """
        self.db = db
        self.es = es
        self.embedding = embedding
        self.chunker = SmartChunker()

        # 初始化解析器
        self.parsers: dict[str, BaseParser] = {
            "md": MarkdownParser(),
            "markdown": MarkdownParser(),
            "pdf": PDFParser(),
        }

    def upload(
        self,
        file_path: str,
        filename: str,
        knowledge_base_id: int,
    ) -> Document:
        """
        上传文档

        Args:
            file_path: 临时文件路径
            filename: 文件名
            knowledge_base_id: 知识库 ID

        Returns:
            创建的文档记录
        """
        # 验证知识库存在
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise ValueError(f"知识库不存在: {knowledge_base_id}")

        # 获取文件类型（去掉开头的点）
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext not in self.parsers:
            raise ValueError(f"不支持的文件格式: .{ext}")

        # 保存文件
        upload_dir = os.path.join(self.UPLOAD_DIR, str(knowledge_base_id))
        os.makedirs(upload_dir, exist_ok=True)
        saved_path = os.path.join(upload_dir, filename)
        shutil.move(file_path, saved_path)

        # 创建文档记录
        doc = Document(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            file_type=ext.lstrip("."),
            file_size=os.path.getsize(saved_path),
            file_path=saved_path,
            status="pending",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        return doc

    def process(self, document_id: int) -> None:
        """
        处理文档

        Args:
            document_id: 文档 ID
        """
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"文档不存在: {document_id}")

        try:
            # 更新状态为处理中
            doc.status = "processing"
            self.db.commit()

            # 解析文档
            parser = self.parsers.get(doc.file_type)
            if not parser:
                raise ValueError(f"不支持的文件类型: {doc.file_type}")

            parsed = parser.parse(doc.file_path)

            # 切片
            chunks = self.chunker.chunk(parsed.content, str(doc.id))

            # 向量化
            texts = [c.content for c in chunks]
            embeddings = self.embedding.embed_texts(texts)

            # 保存到数据库和 ES
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # 保存到 MySQL
                from app.models.chunk import Chunk as ChunkModel
                db_chunk = ChunkModel(
                    chunk_id=chunk.chunk_id,
                    document_id=doc.id,
                    knowledge_base_id=doc.knowledge_base_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_offset=chunk.start_offset,
                    end_offset=chunk.end_offset,
                    section_title=chunk.section_title,
                )
                self.db.add(db_chunk)

                # 保存到 ES
                self.es.index_chunk(
                    chunk_id=chunk.chunk_id,
                    document_id=str(doc.id),
                    knowledge_base_id=str(doc.knowledge_base_id),
                    content=chunk.content,
                    embedding=embedding,
                    metadata={
                        "start_offset": chunk.start_offset,
                        "end_offset": chunk.end_offset,
                        "chunk_index": chunk.chunk_index,
                        "section_title": chunk.section_title,
                    },
                )

            # 更新文档状态
            doc.status = "completed"
            doc.chunk_count = len(chunks)
            self.db.commit()

        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            self.db.commit()
            raise

    def delete(self, document_id: int) -> bool:
        """
        删除文档

        Args:
            document_id: 文档 ID

        Returns:
            是否删除成功
        """
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False

        # 删除 ES 中的 chunks
        self.es.delete_chunks_by_document(str(document_id))

        # 删除 MySQL 中的 chunks
        from app.models.chunk import Chunk as ChunkModel
        self.db.query(ChunkModel).filter(ChunkModel.document_id == document_id).delete()

        # 删除文件
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        # 删除数据库记录
        self.db.delete(doc)
        self.db.commit()

        return True

    def get_by_id(self, document_id: int) -> Optional[Document]:
        """
        根据 ID 获取文档

        Args:
            document_id: 文档 ID

        Returns:
            文档或 None
        """
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_by_knowledge_base(
        self,
        knowledge_base_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[List[Document], int]:
        """
        列出知识库的文档

        Args:
            knowledge_base_id: 知识库 ID
            page: 页码
            page_size: 每页数量

        Returns:
            文档列表和总数
        """
        query = self.db.query(Document).filter(Document.knowledge_base_id == knowledge_base_id)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total
