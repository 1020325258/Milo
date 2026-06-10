"""
对话服务

提供对话的 CRUD 操作。
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationService:
    """对话服务"""

    def __init__(self, db: Session, user_id: str) -> None:
        """
        初始化服务

        Args:
            db: 数据库会话
            user_id: 当前用户 ID
        """
        self.db = db
        self.user_id = user_id

    def create(
        self,
        title: str = "新对话",
        knowledge_base_id: Optional[int] = None,
    ) -> Conversation:
        """
        创建对话

        Args:
            title: 对话标题
            knowledge_base_id: 知识库 ID

        Returns:
            创建的对话
        """
        conversation = Conversation(
            user_id=self.user_id,
            title=title,
            knowledge_base_id=knowledge_base_id,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """
        根据 ID 获取对话

        Args:
            conversation_id: 对话 ID

        Returns:
            对话或 None
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == self.user_id)
            .first()
        )

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> tuple[List[Conversation], int]:
        """
        列出对话

        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词

        Returns:
            对话列表和总数
        """
        query = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == self.user_id)
            .order_by(desc(Conversation.updated_at))
        )

        if search:
            query = query.filter(Conversation.title.contains(search))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def delete(self, conversation_id: int) -> bool:
        """
        删除对话

        Args:
            conversation_id: 对话 ID

        Returns:
            是否删除成功
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return False

        self.db.delete(conversation)
        self.db.commit()
        return True

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        thinking_content: Optional[str] = None,
        references: Optional[dict] = None,
    ) -> Message:
        """
        添加消息

        Args:
            conversation_id: 对话 ID
            role: 角色（user/assistant/system）
            content: 消息内容
            thinking_content: 思考内容
            references: 引用

        Returns:
            创建的消息
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            thinking_content=thinking_content,
            references=references,
        )
        self.db.add(message)

        # 更新对话的更新时间
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(
        self,
        conversation_id: int,
        limit: int = 50,
    ) -> List[Message]:
        """
        获取对话消息

        Args:
            conversation_id: 对话 ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
            .all()
        )

    def get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 10,
    ) -> List[Message]:
        """
        获取最近的消息

        Args:
            conversation_id: 对话 ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .all()
        )

    def update_title(
        self,
        conversation_id: int,
        title: str,
    ) -> Optional[Conversation]:
        """
        更新对话标题

        Args:
            conversation_id: 对话 ID
            title: 新标题

        Returns:
            更新后的对话或 None
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def batch_delete(self, conversation_ids: List[int]) -> int:
        """
        批量删除对话

        Args:
            conversation_ids: 对话 ID 列表

        Returns:
            删除的数量
        """
        count = (
            self.db.query(Conversation)
            .filter(Conversation.id.in_(conversation_ids))
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return count
