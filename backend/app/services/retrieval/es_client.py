"""
Elasticsearch 客户端封装

提供 ES 索引管理、文档索引、检索等功能。
"""

from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch

from app.core.config import settings


class ESClient:
    """Elasticsearch 客户端封装"""

    CHUNKS_INDEX = "milo_chunks"

    def __init__(self, client: Elasticsearch) -> None:
        """
        初始化客户端

        Args:
            client: Elasticsearch 客户端实例
        """
        self.client = client

    def index_exists(self, index: str) -> bool:
        """
        检查索引是否存在

        Args:
            index: 索引名称

        Returns:
            索引是否存在
        """
        return self.client.indices.exists(index=index)

    def create_chunks_index(self) -> None:
        """创建 chunks 索引"""
        if self.index_exists(self.CHUNKS_INDEX):
            return

        mapping = {
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "knowledge_base_id": {"type": "keyword"},
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart",
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": settings.EMBEDDING_DIMENSION,
                        "index": True,
                        "similarity": "cosine",
                        "index_options": {
                            "type": "hnsw",
                            "m": 16,
                            "ef_construction": 100,
                        },
                    },
                    "metadata": {
                        "properties": {
                            "start_offset": {"type": "integer"},
                            "end_offset": {"type": "integer"},
                            "chunk_index": {"type": "integer"},
                            "section_title": {"type": "keyword"},
                        },
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "1s",
                "analysis": {
                    "analyzer": {
                        "ik_max_word": {
                            "type": "custom",
                            "tokenizer": "ik_max_word",
                        },
                        "ik_smart": {
                            "type": "custom",
                            "tokenizer": "ik_smart",
                        },
                    },
                },
            },
        }

        self.client.indices.create(index=self.CHUNKS_INDEX, body=mapping)

    def index_chunk(
        self,
        chunk_id: str,
        document_id: str,
        knowledge_base_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        索引单个 chunk

        Args:
            chunk_id: chunk ID
            document_id: 文档 ID
            knowledge_base_id: 知识库 ID
            content: 文本内容
            embedding: 向量
            metadata: 元数据
        """
        doc = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "knowledge_base_id": knowledge_base_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": "now",
            "updated_at": "now",
        }

        self.client.index(
            index=self.CHUNKS_INDEX,
            id=chunk_id,
            document=doc,
        )

    def index_chunks_bulk(
        self,
        chunks: List[Dict[str, Any]],
    ) -> None:
        """
        批量索引 chunks

        Args:
            chunks: chunk 列表
        """
        if not chunks:
            return

        actions = []
        for chunk in chunks:
            actions.append({"index": {"_index": self.CHUNKS_INDEX, "_id": chunk["chunk_id"]}})
            actions.append(chunk)

        self.client.bulk(operations=actions)

    def delete_chunks_by_document(self, document_id: str) -> None:
        """
        删除文档的所有 chunks

        Args:
            document_id: 文档 ID
        """
        query = {
            "query": {
                "term": {"document_id": document_id}
            }
        }

        self.client.delete_by_query(
            index=self.CHUNKS_INDEX,
            body=query,
        )

    def delete_chunks_by_knowledge_base(self, knowledge_base_id: str) -> None:
        """
        删除知识库的所有 chunks

        Args:
            knowledge_base_id: 知识库 ID
        """
        query = {
            "query": {
                "term": {"knowledge_base_id": knowledge_base_id}
            }
        }

        self.client.delete_by_query(
            index=self.CHUNKS_INDEX,
            body=query,
        )

    def search_vector(
        self,
        embedding: List[float],
        top_k: int = 20,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量检索

        Args:
            embedding: 查询向量
            top_k: 返回数量
            knowledge_base_id: 知识库 ID 过滤
            document_id: 文档 ID 过滤

        Returns:
            检索结果列表
        """
        query = {
            "knn": {
                "field": "embedding",
                "query_vector": embedding,
                "k": top_k,
                "num_candidates": top_k * 10,
            },
            "_source": ["chunk_id", "document_id", "knowledge_base_id", "content", "metadata"],
        }

        # 添加过滤条件
        filters = []
        if knowledge_base_id:
            filters.append({"term": {"knowledge_base_id": knowledge_base_id}})
        if document_id:
            filters.append({"term": {"document_id": document_id}})

        if filters:
            query["knn"]["filter"] = {"bool": {"must": filters}}

        response = self.client.search(
            index=self.CHUNKS_INDEX,
            body=query,
        )

        return self._parse_search_results(response)

    def search_bm25(
        self,
        query_text: str,
        top_k: int = 20,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        BM25 全文检索

        Args:
            query_text: 查询文本
            top_k: 返回数量
            knowledge_base_id: 知识库 ID 过滤
            document_id: 文档 ID 过滤

        Returns:
            检索结果列表
        """
        must = [
            {
                "match": {
                    "content": {
                        "query": query_text,
                        "analyzer": "ik_smart",
                    }
                }
            }
        ]

        if knowledge_base_id:
            must.append({"term": {"knowledge_base_id": knowledge_base_id}})
        if document_id:
            must.append({"term": {"document_id": document_id}})

        query = {
            "query": {
                "bool": {"must": must}
            },
            "size": top_k,
            "_source": ["chunk_id", "document_id", "knowledge_base_id", "content", "metadata"],
        }

        response = self.client.search(
            index=self.CHUNKS_INDEX,
            body=query,
        )

        return self._parse_search_results(response)

    def search_hybrid(
        self,
        query_text: str,
        embedding: List[float],
        top_k: int = 20,
        knowledge_base_id: Optional[str] = None,
        document_id: Optional[str] = None,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        混合检索（向量 + BM25 + RRF）

        Args:
            query_text: 查询文本
            embedding: 查询向量
            top_k: 返回数量
            knowledge_base_id: 知识库 ID 过滤
            document_id: 文档 ID 过滤
            rrf_k: RRF 参数 k

        Returns:
            检索结果列表
        """
        # 构建过滤条件
        filters = []
        if knowledge_base_id:
            filters.append({"term": {"knowledge_base_id": knowledge_base_id}})
        if document_id:
            filters.append({"term": {"document_id": document_id}})

        filter_clause = {"bool": {"must": filters}} if filters else None

        # 向量检索子查询
        knn_query = {
            "field": "embedding",
            "query_vector": embedding,
            "k": top_k,
            "num_candidates": top_k * 10,
        }
        if filter_clause:
            knn_query["filter"] = filter_clause

        # BM25 子查询
        bm25_must = [
            {
                "match": {
                    "content": {
                        "query": query_text,
                    }
                }
            }
        ]
        if filters:
            bm25_must.extend(filters)

        bm25_query = {
            "bool": {"must": bm25_must}
        }

        # 混合查询（使用 knn + query）
        query = {
            "knn": knn_query,
            "query": bm25_query,
            "size": top_k,
            "_source": ["chunk_id", "document_id", "knowledge_base_id", "content", "metadata"],
        }

        response = self.client.search(
            index=self.CHUNKS_INDEX,
            body=query,
        )

        return self._parse_search_results(response)

    def _parse_search_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析搜索结果

        Args:
            response: ES 搜索响应

        Returns:
            解析后的结果列表
        """
        results = []

        for hit in response.get("hits", {}).get("hits", []):
            source = hit["_source"]
            results.append({
                "chunk_id": source["chunk_id"],
                "document_id": source["document_id"],
                "knowledge_base_id": source["knowledge_base_id"],
                "content": source["content"],
                "metadata": source.get("metadata", {}),
                "score": hit.get("_score", 0),
            })

        return results
