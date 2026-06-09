"""
对话服务单元测试
"""

from unittest.mock import MagicMock

import pytest

from app.models.conversation import Conversation
from app.models.message import Message
from app.services.conversation.service import ConversationService


class TestConversationService:
    """对话服务测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ConversationService(self.mock_db)

    def test_create(self) -> None:
        """测试创建对话"""
        result = self.service.create(title="测试对话", knowledge_base_id=1)

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        assert result.title == "测试对话"

    def test_get_by_id(self) -> None:
        """测试根据 ID 获取对话"""
        mock_conversation = Conversation(id=1, title="测试对话")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

        result = self.service.get_by_id(1)

        assert result == mock_conversation
        assert result.title == "测试对话"

    def test_get_by_id_not_found(self) -> None:
        """测试获取不存在的对话"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_by_id(999)

        assert result is None

    def test_list(self) -> None:
        """测试列出对话"""
        mock_conv1 = Conversation(id=1, title="对话1")
        mock_conv2 = Conversation(id=2, title="对话2")

        self.mock_db.query.return_value.order_by.return_value.count.return_value = 2
        self.mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_conv1,
            mock_conv2,
        ]

        items, total = self.service.list(page=1, page_size=10)

        assert total == 2
        assert len(items) == 2

    def test_list_with_search(self) -> None:
        """测试搜索对话"""
        mock_conv = Conversation(id=1, title="测试对话")
        self.mock_db.query.return_value.order_by.return_value.filter.return_value.count.return_value = 1
        self.mock_db.query.return_value.order_by.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_conv,
        ]

        items, total = self.service.list(search="测试")

        assert total == 1
        assert len(items) == 1

    def test_delete(self) -> None:
        """测试删除对话"""
        mock_conversation = Conversation(id=1, title="测试对话")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

        result = self.service.delete(1)

        assert result is True
        self.mock_db.delete.assert_called_once_with(mock_conversation)
        self.mock_db.commit.assert_called_once()

    def test_delete_not_found(self) -> None:
        """测试删除不存在的对话"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.delete(999)

        assert result is False

    def test_add_message(self) -> None:
        """测试添加消息"""
        mock_conversation = Conversation(id=1, title="测试对话")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

        result = self.service.add_message(
            conversation_id=1,
            role="user",
            content="测试消息",
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        assert result.role == "user"
        assert result.content == "测试消息"

    def test_get_messages(self) -> None:
        """测试获取消息"""
        mock_msg1 = Message(id=1, conversation_id=1, role="user", content="消息1")
        mock_msg2 = Message(id=2, conversation_id=1, role="assistant", content="消息2")

        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_msg1,
            mock_msg2,
        ]

        messages = self.service.get_messages(conversation_id=1, limit=10)

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_update_title(self) -> None:
        """测试更新标题"""
        mock_conversation = Conversation(id=1, title="旧标题")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

        result = self.service.update_title(1, "新标题")

        assert result.title == "新标题"
        self.mock_db.commit.assert_called_once()

    def test_update_title_not_found(self) -> None:
        """测试更新不存在的对话标题"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.update_title(999, "新标题")

        assert result is None

    def test_batch_delete(self) -> None:
        """测试批量删除"""
        self.mock_db.query.return_value.filter.return_value.delete.return_value = 3

        count = self.service.batch_delete([1, 2, 3])

        assert count == 3
        self.mock_db.commit.assert_called_once()
