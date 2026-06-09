"""
知识库服务单元测试
"""

from unittest.mock import MagicMock

import pytest

from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.knowledge.service import KnowledgeBaseService


class TestKnowledgeBaseService:
    """知识库服务测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = KnowledgeBaseService(self.mock_db)

    def test_create(self) -> None:
        """测试创建知识库"""
        data = KnowledgeBaseCreate(
            name="测试知识库",
            description="测试描述",
            embedding_model="text-embedding-v3",
        )

        # Mock 数据库操作
        mock_kb = KnowledgeBase(
            id=1,
            name="测试知识库",
            description="测试描述",
            embedding_model="text-embedding-v3",
        )
        self.mock_db.refresh.return_value = None

        result = self.service.create(data)

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_get_by_id(self) -> None:
        """测试根据 ID 获取知识库"""
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_kb

        result = self.service.get_by_id(1)

        assert result == mock_kb
        assert result.name == "测试知识库"

    def test_get_by_id_not_found(self) -> None:
        """测试获取不存在的知识库"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_by_id(999)

        assert result is None

    def test_get_by_name(self) -> None:
        """测试根据名称获取知识库"""
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_kb

        result = self.service.get_by_name("测试知识库")

        assert result == mock_kb

    def test_list(self) -> None:
        """测试列出知识库"""
        mock_kb1 = KnowledgeBase(id=1, name="知识库1")
        mock_kb2 = KnowledgeBase(id=2, name="知识库2")

        self.mock_db.query.return_value.count.return_value = 2
        self.mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_kb1,
            mock_kb2,
        ]

        items, total = self.service.list(page=1, page_size=10)

        assert total == 2
        assert len(items) == 2

    def test_list_with_search(self) -> None:
        """测试搜索知识库"""
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        self.mock_db.query.return_value.filter.return_value.count.return_value = 1
        self.mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_kb,
        ]

        items, total = self.service.list(search="测试")

        assert total == 1
        assert len(items) == 1

    def test_update(self) -> None:
        """测试更新知识库"""
        mock_kb = KnowledgeBase(id=1, name="旧名称")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_kb

        data = KnowledgeBaseUpdate(name="新名称")
        result = self.service.update(1, data)

        assert result.name == "新名称"
        self.mock_db.commit.assert_called_once()

    def test_update_not_found(self) -> None:
        """测试更新不存在的知识库"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        data = KnowledgeBaseUpdate(name="新名称")
        result = self.service.update(999, data)

        assert result is None

    def test_delete(self) -> None:
        """测试删除知识库"""
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_kb

        result = self.service.delete(1)

        assert result is True
        self.mock_db.delete.assert_called_once_with(mock_kb)
        self.mock_db.commit.assert_called_once()

    def test_delete_not_found(self) -> None:
        """测试删除不存在的知识库"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.delete(999)

        assert result is False
