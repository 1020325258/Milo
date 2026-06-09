"""
Agent 服务单元测试
"""

from unittest.mock import MagicMock

import pytest

from app.services.agent.service import AgentService
from app.services.retrieval.reranker import RerankResult


class TestAgentService:
    """Agent 服务测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.mock_retriever = MagicMock()
        self.mock_embedding = MagicMock()

        self.service = AgentService(
            retriever=self.mock_retriever,
            embedding=self.mock_embedding,
        )

    def test_build_context(self) -> None:
        """测试构建上下文"""
        results = [
            RerankResult(
                chunk_id="chunk_001",
                document_id="doc_001",
                knowledge_base_id="kb_001",
                content="内容1",
                metadata={},
                original_score=0.8,
                rerank_score=0.95,
            ),
            RerankResult(
                chunk_id="chunk_002",
                document_id="doc_002",
                knowledge_base_id="kb_001",
                content="内容2",
                metadata={},
                original_score=0.7,
                rerank_score=0.85,
            ),
        ]

        context = self.service._build_context(results)

        assert "[1] 内容1" in context
        assert "[2] 内容2" in context

    def test_build_context_empty(self) -> None:
        """测试构建空上下文"""
        context = self.service._build_context([])

        assert context == ""

    def test_build_prompt(self) -> None:
        """测试构建 Prompt"""
        context = "[1] 测试内容"
        query = "测试查询"

        prompt = self.service._build_prompt(query, context)

        # 验证 Prompt 包含必要信息
        assert "测试查询" in prompt
        assert "测试内容" in prompt

    def test_build_prompt_with_history(self) -> None:
        """测试带历史的 Prompt"""
        context = "[1] 测试内容"
        query = "测试查询"
        history = [
            {"role": "user", "content": "历史问题"},
            {"role": "assistant", "content": "历史回答"},
        ]

        prompt = self.service._build_prompt(query, context, history)

        assert "历史问题" in prompt
        assert "历史回答" in prompt

    def test_generate_response_with_results(self) -> None:
        """测试生成响应（有结果）"""
        results = [
            RerankResult(
                chunk_id="chunk_001",
                document_id="doc_001",
                knowledge_base_id="kb_001",
                content="测试内容",
                metadata={},
                original_score=0.8,
                rerank_score=0.95,
            ),
        ]

        response = self.service._generate_response("prompt", results)

        assert "测试内容" in response
        assert "[1]" in response

    def test_generate_response_no_results(self) -> None:
        """测试生成响应（无结果）"""
        response = self.service._generate_response("prompt", [])

        assert "抱歉" in response

    def test_build_references(self) -> None:
        """测试构建引用"""
        results = [
            RerankResult(
                chunk_id="chunk_001",
                document_id="doc_001",
                knowledge_base_id="kb_001",
                content="测试内容",
                metadata={},
                original_score=0.8,
                rerank_score=0.95,
            ),
        ]

        references = self.service.build_references(results)

        assert len(references) == 1
        assert references[0]["index"] == 1
        assert references[0]["chunk_id"] == "chunk_001"
        assert references[0]["relevance_score"] == 0.95
