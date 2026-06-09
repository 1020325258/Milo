#!/usr/bin/env python3
"""
Elasticsearch 索引初始化脚本

用于创建 Milo 知识库系统所需的 Elasticsearch 索引和映射。

使用方法:
    python scripts/init_elasticsearch.py

环境变量:
    ELASTICSEARCH_URL: Elasticsearch 地址（默认 http://localhost:9200）
    ELASTICSEARCH_USERNAME: 用户名（可选）
    ELASTICSEARCH_PASSWORD: 密码（可选）
    EMBEDDING_DIMENSION: 向量维度（默认 1024）
"""

import os
import sys

from elasticsearch import Elasticsearch

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 配置
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

# 索引名称
CHUNKS_INDEX = "milo_chunks"

# Chunks 索引映射
CHUNKS_MAPPING = {
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
                "dims": EMBEDDING_DIMENSION,
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


def get_es_client() -> Elasticsearch:
    """创建 Elasticsearch 客户端"""
    kwargs = {"hosts": [ELASTICSEARCH_URL], "request_timeout": 30}

    if ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD:
        kwargs["basic_auth"] = (ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)

    return Elasticsearch(**kwargs)


def create_chunks_index(client: Elasticsearch) -> None:
    """创建 chunks 索引"""
    if client.indices.exists(index=CHUNKS_INDEX):
        print(f"索引 {CHUNKS_INDEX} 已存在，跳过创建")
        return

    client.indices.create(index=CHUNKS_INDEX, body=CHUNKS_MAPPING)
    print(f"✓ 创建索引 {CHUNKS_INDEX}")


def main() -> None:
    """主函数"""
    print(f"连接到 Elasticsearch: {ELASTICSEARCH_URL}")

    try:
        client = get_es_client()
        if not client.ping():
            print("✗ 无法连接到 Elasticsearch")
            sys.exit(1)
        print("✓ 连接成功")

        print("\n创建索引...")
        create_chunks_index(client)

        print("\n✓ Elasticsearch 初始化完成")

    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
