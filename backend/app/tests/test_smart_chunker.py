"""
智能切片器单元测试
"""

import pytest

from app.services.chunking.smart_chunker import SmartChunker


class TestSmartChunker:
    """智能切片器测试"""

    def setup_method(self) -> None:
        """测试前准备"""
        self.chunker = SmartChunker(
            max_chunk_size=100,  # 使用较小的值便于测试
            overlap=20,
            min_chunk_size=30,
        )

    def test_chunk_with_headers(self) -> None:
        """测试按标题切分"""
        text = """# 第一章

这是第一章的内容，包含一些测试文本。

## 1.1 小节

这是 1.1 小节的内容。

## 1.2 小节

这是 1.2 小节的内容。

# 第二章

这是第二章的内容。
"""
        chunks = self.chunker.chunk(text, "doc_001")

        assert len(chunks) > 0
        # 验证每个 chunk 都有正确的属性
        for chunk in chunks:
            assert chunk.chunk_id
            assert chunk.content
            assert chunk.chunk_index >= 0
            assert chunk.start_offset >= 0
            assert chunk.end_offset > chunk.start_offset

    def test_chunk_without_headers(self) -> None:
        """测试无标题文档"""
        text = "这是一段没有标题的文本。" * 100

        chunks = self.chunker.chunk(text, "doc_002")

        assert len(chunks) > 0
        # 验证回退到固定 Token 切片
        for chunk in chunks:
            assert chunk.chunk_id
            assert chunk.content

    def test_short_text(self) -> None:
        """测试短文本"""
        text = "这是一段很短的文本。"

        chunks = self.chunker.chunk(text, "doc_003")

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_id_generation(self) -> None:
        """测试 chunk ID 生成"""
        id1 = self.chunker._generate_chunk_id("doc1", 0)
        id2 = self.chunker._generate_chunk_id("doc1", 1)
        id3 = self.chunker._generate_chunk_id("doc2", 0)

        # 同一文档不同索引应该不同
        assert id1 != id2
        # 不同文档同一索引应该不同
        assert id1 != id3

    def test_merge_short_chunks(self) -> None:
        """测试短 chunk 合并"""
        from app.services.chunking.chunker import Chunk

        chunks = [
            Chunk(
                chunk_id="1",
                content="短文本",
                chunk_index=0,
                start_offset=0,
                end_offset=3,
            ),
            Chunk(
                chunk_id="2",
                content="另一个短文本",
                chunk_index=1,
                start_offset=4,
                end_offset=10,
            ),
            Chunk(
                chunk_id="3",
                content="这是一个足够长的文本，应该不会被合并。" * 10,
                chunk_index=2,
                start_offset=11,
                end_offset=100,
            ),
        ]

        merged = self.chunker._merge_short_chunks(chunks)

        # 前两个短 chunk 应该被合并
        assert len(merged) < len(chunks)

    def test_split_by_headers(self) -> None:
        """测试标题分割"""
        text = """# 标题一

内容一

## 标题二

内容二

### 标题三

内容三
"""
        sections = self.chunker._split_by_headers(text)

        # 应该识别出 # 和 ## 标题
        assert len(sections) >= 2

        # 验证标题被正确提取
        titles = [s["title"] for s in sections if s["title"]]
        assert "标题一" in titles
        assert "标题二" in titles
