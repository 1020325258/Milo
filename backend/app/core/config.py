"""
应用配置管理

使用 pydantic-settings 管理应用配置，支持从环境变量和 .env 文件加载。
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "milo"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/milo"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None

    # DashScope
    DASHSCOPE_API_KEY: str = ""

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Embedding
    EMBEDDING_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIMENSION: int = 1024

    # Chunking
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 100
    MIN_CHUNK_SIZE: int = 100

    # Retrieval
    RETRIEVAL_TOP_K: int = 20
    RERANK_TOP_K: int = 5
    RRF_K: int = 60

    # LLM
    LLM_MODEL: str = "qwen-max"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.APP_ENV == "production"


# 创建全局配置实例
settings = Settings()
