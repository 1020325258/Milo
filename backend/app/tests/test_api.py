"""
API 集成测试
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端"""
    return TestClient(app)


class TestHealthAPI:
    """健康检查 API 测试"""

    def test_health_check(self, client: TestClient) -> None:
        """测试基本健康检查"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "milo"


class TestKnowledgeAPI:
    """知识库 API 测试"""

    @patch("app.api.knowledge.KnowledgeBaseService")
    def test_create_knowledge_base(self, mock_service_class: MagicMock, client: TestClient) -> None:
        """测试创建知识库"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_by_name.return_value = None

        from app.models.knowledge_base import KnowledgeBase
        mock_kb = KnowledgeBase(
            id=1,
            name="测试知识库",
            description="测试描述",
            embedding_model="text-embedding-v3",
        )
        mock_service.create.return_value = mock_kb

        response = client.post(
            "/api/knowledge/",
            json={
                "name": "测试知识库",
                "description": "测试描述",
                "embedding_model": "text-embedding-v3",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试知识库"

    @patch("app.api.knowledge.KnowledgeBaseService")
    def test_create_knowledge_base_duplicate_name(self, mock_service_class: MagicMock, client: TestClient) -> None:
        """测试创建重复名称的知识库"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        from app.models.knowledge_base import KnowledgeBase
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        mock_service.get_by_name.return_value = mock_kb

        response = client.post(
            "/api/knowledge/",
            json={"name": "测试知识库"},
        )

        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]

    @patch("app.api.knowledge.KnowledgeBaseService")
    def test_list_knowledge_bases(self, mock_service_class: MagicMock, client: TestClient) -> None:
        """测试列出知识库"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        from app.models.knowledge_base import KnowledgeBase
        mock_kb1 = KnowledgeBase(id=1, name="知识库1")
        mock_kb2 = KnowledgeBase(id=2, name="知识库2")
        mock_service.list.return_value = ([mock_kb1, mock_kb2], 2)

        response = client.get("/api/knowledge/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @patch("app.api.knowledge.KnowledgeBaseService")
    def test_get_knowledge_base(self, mock_service_class: MagicMock, client: TestClient) -> None:
        """测试获取知识库详情"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        from app.models.knowledge_base import KnowledgeBase
        mock_kb = KnowledgeBase(id=1, name="测试知识库")
        mock_service.get_by_id.return_value = mock_kb

        response = client.get("/api/knowledge/1")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试知识库"

    @patch("app.api.knowledge.KnowledgeBaseService")
    def test_get_knowledge_base_not_found(self, mock_service_class: MagicMock, client: TestClient) -> None:
        """测试获取不存在的知识库"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_by_id.return_value = None

        response = client.get("/api/knowledge/999")

        assert response.status_code == 404

    @patch("app.api.knowledge.KnowledgeBaseService")
    def test_delete_knowledge_base(self, mock_service_class: MagicMock, client: TestClient) -> None:
        """测试删除知识库"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.delete.return_value = True

        response = client.delete("/api/knowledge/1")

        assert response.status_code == 204


class TestChatAPI:
    """对话 API 测试"""

    @patch("app.api.chat.ConversationService")
    @patch("app.api.chat.AgentService")
    def test_chat(self, mock_agent_class: MagicMock, mock_conv_class: MagicMock, client: TestClient) -> None:
        """测试对话"""
        mock_conv_service = MagicMock()
        mock_conv_class.return_value = mock_conv_service

        from app.models.conversation import Conversation
        from app.models.message import Message

        mock_conv = Conversation(id=1, title="测试对话")
        mock_conv_service.create.return_value = mock_conv
        mock_conv_service.get_recent_messages.return_value = []

        mock_msg = Message(id=1, conversation_id=1, role="assistant", content="测试回答")
        mock_conv_service.add_message.return_value = mock_msg

        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        async def mock_chat(*args, **kwargs):
            yield "测试回答"

        mock_agent.chat.return_value = mock_chat()
        mock_agent.build_references.return_value = []

        response = client.post(
            "/api/chat/",
            json={"message": "测试问题"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == 1
        assert data["message"]["content"] == "测试回答"
