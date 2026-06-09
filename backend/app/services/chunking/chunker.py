"""
切片器基类

定义文本切片的抽象接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Chunk:
    """文本切片"""

    chunk_id: str
    content: str
    chunk_index: int
    start_offset: int
    end_offset: int
    section_title: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseChunker(ABC):
    """切片器基类"""

    @abstractmethod
    def chunk(self, text: str, document_id: str) -> List[Chunk]:
        """
        将文本切分为片段

        Args:
            text: 原始文本
            document_id: 文档 ID

        Returns:
            切片列表
        """
        pass

    @abstractmethod
    def chunk_with_sections(
        self, text: str, document_id: str
    ) -> List[Chunk]:
        """
        按章节切分文本

        Args:
            text: 原始文本
            document_id: 文档 ID

        Returns:
            切片列表
        """
        pass
