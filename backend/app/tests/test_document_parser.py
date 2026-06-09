"""
文档解析器单元测试
"""

import os
import tempfile

import pytest

from app.services.document.md_parser import MarkdownParser
from app.services.document.parser import ParsedDocument
from app.services.document.pdf_parser import PDFParser


class TestMarkdownParser:
    """Markdown 解析器测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.parser = MarkdownParser()

    def test_supported_extensions(self) -> None:
        """测试支持的扩展名"""
        extensions = self.parser.supported_extensions()
        assert ".md" in extensions
        assert ".markdown" in extensions

    def test_parse_simple_markdown(self) -> None:
        """测试解析简单 Markdown"""
        content = """# 测试标题

这是一个测试段落。

## 二级标题

- 列表项 1
- 列表项 2
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert isinstance(result, ParsedDocument)
            assert result.file_type == "markdown"
            assert "测试标题" in result.content
            assert result.metadata.get("title") == "测试标题"
            assert len(result.metadata.get("headers", [])) == 2
        finally:
            os.unlink(temp_path)

    def test_parse_markdown_with_front_matter(self) -> None:
        """测试解析带 front matter 的 Markdown"""
        content = """---
title: 测试文档
author: 测试作者
---

# 正文标题

正文内容。
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert result.metadata.get("title") == "测试文档"
            assert result.metadata.get("author") == "测试作者"
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self) -> None:
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("/nonexistent/file.md")

    def test_unsupported_extension(self) -> None:
        """测试不支持的扩展名"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                self.parser.parse(temp_path)
        finally:
            os.unlink(temp_path)


class TestPDFParser:
    """PDF 解析器测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.parser = PDFParser()

    def test_supported_extensions(self) -> None:
        """测试支持的扩展名"""
        extensions = self.parser.supported_extensions()
        assert ".pdf" in extensions

    def test_file_not_found(self) -> None:
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("/nonexistent/file.pdf")

    def test_unsupported_extension(self) -> None:
        """测试不支持的扩展名"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                self.parser.parse(temp_path)
        finally:
            os.unlink(temp_path)
