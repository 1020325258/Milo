"""
Markdown 解析器

解析 Markdown 文件为纯文本，保留结构信息。
"""

import os
import re
from typing import List, Tuple

from markdown_it import MarkdownIt

from app.services.document.parser import BaseParser, ParsedDocument


class MarkdownParser(BaseParser):
    """Markdown 解析器"""

    def __init__(self) -> None:
        """初始化解析器"""
        self.md = MarkdownIt("commonmark", {"breaks": True}).enable("table")

    def supported_extensions(self) -> List[str]:
        """支持的文件扩展名"""
        return [".md", ".markdown", ".mdown", ".mkd"]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 Markdown 文件

        Args:
            file_path: 文件路径

        Returns:
            解析后的文档
        """
        self.validate_file(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取元数据
        metadata = self._extract_metadata(content)

        # 转换为纯文本
        text = self._convert_to_text(content)

        return ParsedDocument(
            content=text,
            metadata=metadata,
            file_type="markdown",
            filename=os.path.basename(file_path),
        )

    def _extract_metadata(self, content: str) -> dict:
        """
        提取 Markdown 元数据

        Args:
            content: Markdown 内容

        Returns:
            元数据字典
        """
        metadata = {}

        # 提取标题
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # 提取 YAML front matter
        front_matter_match = re.search(r"^---\n(.+?)\n---\n", content, re.DOTALL)
        if front_matter_match:
            try:
                import yaml

                metadata.update(yaml.safe_load(front_matter_match.group(1)))
            except Exception:
                pass

        # 提取所有标题作为目录
        headers = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        if headers:
            metadata["headers"] = [
                {"level": len(h[0]), "text": h[1].strip()} for h in headers
            ]

        return metadata

    def _convert_to_text(self, content: str) -> str:
        """
        将 Markdown 转换为纯文本

        Args:
            content: Markdown 内容

        Returns:
            纯文本
        """
        # 移除 YAML front matter
        content = re.sub(r"^---\n.+?\n---\n", "", content, flags=re.DOTALL)

        # 移除图片
        content = re.sub(r"!\[.*?\]\(.*?\)", "", content)

        # 移除链接，保留文本
        content = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", content)

        # 移除 HTML 标签
        content = re.sub(r"<[^>]+>", "", content)

        # 移除代码块
        content = re.sub(r"```[\s\S]*?```", "", content)

        # 移除行内代码
        content = re.sub(r"`[^`]+`", "", content)

        # 移除粗体和斜体标记
        content = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", content)
        content = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", content)

        # 移除删除线
        content = re.sub(r"~~(.*?)~~", r"\1", content)

        # 移除标题标记
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

        # 移除水平线
        content = re.sub(r"^[-*_]{3,}\s*$", "", content, flags=re.MULTILINE)

        # 移除列表标记
        content = re.sub(r"^[\s]*[-*+]\s+", "", content, flags=re.MULTILINE)
        content = re.sub(r"^[\s]*\d+\.\s+", "", content, flags=re.MULTILINE)

        # 清理多余空行
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()
