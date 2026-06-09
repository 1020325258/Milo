"""
文档服务单元测试
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.services.document.service import DocumentService


class TestDocumentService:
    """文档服务测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.mock_db = MagicMock()
        self.mock_es = MagicMock()
        self.mock_embedding = MagicMock()

        self.service = DocumentService(
            db=self.mock_db,
            es=self.mock_es,
            embedding=self.mock_embedding,
        )

    def test_upload_success(self) -> None:
        """测试成功上传文档"""
        # Mock 知识库存在
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_kb

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            f.write(b"# Test")
            temp_path = f.name

        try:
            result = self.service.upload(
                file_path=temp_path,
                filename="test.md",
                knowledge_base_id=1,
            )

            assert result.filename == "test.md"
            assert result.file_type == ".md"
            assert result.status == "pending"
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
        finally:
            # 清理
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_upload_knowledge_base_not_found(self) -> None:
        """测试上传到不存在的知识库"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="知识库不存在"):
            self.service.upload(
                file_path="/tmp/test.md",
                filename="test.md",
                knowledge_base_id=999,
            )

    def test_upload_unsupported_format(self) -> None:
        """测试上传不支持的格式"""
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_kb

        with pytest.raises(ValueError, match="不支持的文件格式"):
            self.service.upload(
                file_path="/tmp/test.txt",
                filename="test.txt",
                knowledge_base_id=1,
            )

    def test_delete_success(self) -> None:
        """测试成功删除文档"""
        mock_doc = Document(
            id=1,
            filename="test.md",
            file_path="/uploads/1/test.md",
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

        with patch("os.path.exists", return_value=True), patch("os.remove"):
            result = self.service.delete(1)

        assert result is True
        self.mock_es.delete_chunks_by_document.assert_called_once_with("1")
        self.mock_db.delete.assert_called_once_with(mock_doc)
        self.mock_db.commit.assert_called_once()

    def test_delete_not_found(self) -> None:
        """测试删除不存在的文档"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.delete(999)

        assert result is False

    def test_get_by_id(self) -> None:
        """测试根据 ID 获取文档"""
        mock_doc = Document(id=1, filename="test.md")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

        result = self.service.get_by_id(1)

        assert result == mock_doc
        assert result.filename == "test.md"

    def test_list_by_knowledge_base(self) -> None:
        """测试列出知识库的文档"""
        mock_doc1 = Document(id=1, filename="test1.md")
        mock_doc2 = Document(id=2, filename="test2.md")

        self.mock_db.query.return_value.filter.return_value.count.return_value = 2
        self.mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_doc1,
            mock_doc2,
        ]

        items, total = self.service.list_by_knowledge_base(
            knowledge_base_id=1,
            page=1,
            page_size=10,
        )

        assert total == 2
        assert len(items) == 2
