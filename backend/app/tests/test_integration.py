"""
端到端集成测试
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.base import Base


# 使用 SQLite 内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    # 创建测试数据库表
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # 清理
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


class TestKnowledgeBaseIntegration:
    """知识库集成测试"""

    def test_create_and_get(self, client: TestClient) -> None:
        """测试创建和获取知识库"""
        # 创建
        response = client.post(
            "/api/knowledge/",
            json={
                "name": "集成测试知识库",
                "description": "用于集成测试",
            },
        )
        assert response.status_code == 201
        data = response.json()
        kb_id = data["id"]
        assert data["name"] == "集成测试知识库"

        # 获取
        response = client.get(f"/api/knowledge/{kb_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "集成测试知识库"

    def test_list_knowledge_bases(self, client: TestClient) -> None:
        """测试列出知识库"""
        response = client.get("/api/knowledge/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_update_knowledge_base(self, client: TestClient) -> None:
        """测试更新知识库"""
        # 先获取一个知识库
        response = client.get("/api/knowledge/")
        kb_id = response.json()["items"][0]["id"]

        # 更新
        response = client.put(
            f"/api/knowledge/{kb_id}",
            json={"name": "更新后的名称"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "更新后的名称"

    def test_duplicate_name(self, client: TestClient) -> None:
        """测试重复名称"""
        # 先创建一个
        client.post(
            "/api/knowledge/",
            json={"name": "重复名称测试"},
        )

        # 再创建同名
        response = client.post(
            "/api/knowledge/",
            json={"name": "重复名称测试"},
        )
        assert response.status_code == 400


class TestHealthIntegration:
    """健康检查集成测试"""

    def test_health_check(self, client: TestClient) -> None:
        """测试健康检查"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestDocumentIntegration:
    """文档集成测试"""

    def test_upload_unsupported_format(self, client: TestClient) -> None:
        """测试上传不支持的格式"""
        # 先获取知识库 ID
        response = client.get("/api/knowledge/")
        if response.json()["total"] == 0:
            pytest.skip("需要先创建知识库")

        kb_id = response.json()["items"][0]["id"]

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = client.post(
                    "/api/document/upload",
                    files={"file": ("test.txt", f, "text/plain")},
                    data={"knowledge_base_id": kb_id},
                )
            assert response.status_code == 400
        finally:
            os.unlink(temp_path)
