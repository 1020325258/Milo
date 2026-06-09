"""
文档解析器基类

定义文档解析的抽象接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedDocument:
    """解析后的文档"""

    content: str
    metadata: dict
    file_type: str
    filename: str


class BaseParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        解析文档

        Args:
            file_path: 文件路径

        Returns:
            解析后的文档

        Raises:
            ValueError: 文件格式不支持
            FileNotFoundError: 文件不存在
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """
        支持的文件扩展名

        Returns:
            支持的扩展名列表
        """
        pass

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否有效

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions():
            raise ValueError(f"不支持的文件格式: {ext}")

        return True
