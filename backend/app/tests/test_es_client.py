"""
ES 客户端单元测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.retrieval.es_client import ESClient


class TestESClient:
    """ES 客户端测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.mock_es = MagicMock()
        self.client = ESClient(self.mock_es)

    def test_index_exists(self) -> None:
        """测试索引存在检查"""
        self.mock_es.indices.exists.return_value = True

        result = self.client.index_exists("test_index")

        assert result is True
        self.mock_es.indices.exists.assert_called_once_with(index="test_index")

    def test_create_chunks_index(self) -> None:
        """测试创建 chunks 索引"""
        self.mock_es.indices.exists.return_value = False

        self.client.create_chunks_index()

        self.mock_es.indices.create.assert_called_once()
        call_args = self.mock_es.indices.create.call_args
        assert call_args[1]["index"] == ESClient.CHUNKS_INDEX

    def test_create_chunks_index_already_exists(self) -> None:
        """测试索引已存在时跳过创建"""
        self.mock_es.indices.exists.return_value = True

        self.client.create_chunks_index()

        self.mock_es.indices.create.assert_not_called()

    def test_index_chunk(self) -> None:
        """测试索引单个 chunk"""
        self.client.index_chunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            knowledge_base_id="kb_001",
            content="测试内容",
            embedding=[0.1, 0.2, 0.3],
        )

        self.mock_es.index.assert_called_once()
        call_args = self.mock_es.index.call_args
        assert call_args[1]["index"] == ESClient.CHUNKS_INDEX
        assert call_args[1]["id"] == "chunk_001"

    def test_delete_chunks_by_document(self) -> None:
        """测试删除文档的 chunks"""
        self.client.delete_chunks_by_document("doc_001")

        self.mock_es.delete_by_query.assert_called_once()
        call_args = self.mock_es.delete_by_query.call_args
        assert call_args[1]["index"] == ESClient.CHUNKS_INDEX

    def test_search_vector(self) -> None:
        """测试向量检索"""
        self.mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "chunk_001",
                        "_score": 0.9,
                        "_source": {
                            "chunk_id": "chunk_001",
                            "document_id": "doc_001",
                            "knowledge_base_id": "kb_001",
                            "content": "测试内容",
                            "metadata": {},
                        },
                    }
                ]
            }
        }

        results = self.client.search_vector(
            embedding=[0.1, 0.2, 0.3],
            top_k=10,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_001"
        assert results[0]["score"] == 0.9

    def test_search_bm25(self) -> None:
        """测试 BM25 检索"""
        self.mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "chunk_001",
                        "_score": 1.5,
                        "_source": {
                            "chunk_id": "chunk_001",
                            "document_id": "doc_001",
                            "knowledge_base_id": "kb_001",
                            "content": "测试内容",
                            "metadata": {},
                        },
                    }
                ]
            }
        }

        results = self.client.search_bm25(
            query_text="测试查询",
            top_k=10,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_001"
        assert results[0]["score"] == 1.5

    def test_search_hybrid(self) -> None:
        """测试混合检索"""
        self.mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "chunk_001",
                        "_score": 0.95,
                        "_source": {
                            "chunk_id": "chunk_001",
                            "document_id": "doc_001",
                            "knowledge_base_id": "kb_001",
                            "content": "测试内容",
                            "metadata": {},
                        },
                    }
                ]
            }
        }

        results = self.client.search_hybrid(
            query_text="测试查询",
            embedding=[0.1, 0.2, 0.3],
            top_k=10,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk_001"
        assert results[0]["score"] == 0.95
