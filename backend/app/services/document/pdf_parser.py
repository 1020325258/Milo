"""
PDF 解析器

解析 PDF 文件为纯文本，保留结构信息。
"""

import os
from typing import List

import fitz  # PyMuPDF

from app.services.document.parser import BaseParser, ParsedDocument


class PDFParser(BaseParser):
    """PDF 解析器"""

    def supported_extensions(self) -> List[str]:
        """支持的文件扩展名"""
        return [".pdf"]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 PDF 文件

        Args:
            file_path: 文件路径

        Returns:
            解析后的文档
        """
        self.validate_file(file_path)

        doc = fitz.open(file_path)

        # 提取元数据
        metadata = self._extract_metadata(doc)

        # 提取文本
        text = self._extract_text(doc)

        doc.close()

        return ParsedDocument(
            content=text,
            metadata=metadata,
            file_type="pdf",
            filename=os.path.basename(file_path),
        )

    def _extract_metadata(self, doc: fitz.Document) -> dict:
        """
        提取 PDF 元数据

        Args:
            doc: PDF 文档对象

        Returns:
            元数据字典
        """
        metadata = {}

        # 基本元数据
        meta = doc.metadata
        if meta:
            metadata["title"] = meta.get("title", "")
            metadata["author"] = meta.get("author", "")
            metadata["subject"] = meta.get("subject", "")
            metadata["keywords"] = meta.get("keywords", "")
            metadata["creator"] = meta.get("creator", "")
            metadata["producer"] = meta.get("producer", "")

        # 页面信息
        metadata["page_count"] = len(doc)

        return metadata

    def _extract_text(self, doc: fitz.Document) -> str:
        """
        提取 PDF 文本

        Args:
            doc: PDF 文档对象

        Returns:
            提取的文本
        """
        text_blocks = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                text_blocks.append(f"--- 第 {page_num + 1} 页 ---\n{text}")

        return "\n\n".join(text_blocks)
