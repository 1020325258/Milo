"""
Elasticsearch 连接管理

提供 Elasticsearch 客户端单例。
"""

from typing import Optional

from elasticsearch import Elasticsearch

from app.core.config import settings
from app.services.retrieval.es_client import ESClient

# ES 客户端单例
_es_client: Optional[ESClient] = None


def get_es_client() -> ESClient:
    """获取 ES 客户端单例"""
    global _es_client

    if _es_client is None:
        kwargs = {
            "hosts": [settings.ELASTICSEARCH_URL],
            "request_timeout": 30,
        }

        if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
            kwargs["basic_auth"] = (
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD,
            )

        client = Elasticsearch(**kwargs)
        _es_client = ESClient(client)

    return _es_client
