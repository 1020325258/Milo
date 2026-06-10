"""
智能切片器

基于文档结构的智能切片，自动识别标题并按章节切分。
如果单个章节超过 max_chunk_size，则在章节内部进行二次切分。

策略：
1. 按标题（## 或 #）分割文档
2. 超长 section 二次切分（保留 overlap）
3. 无标题文档回退到固定 Token 切片
4. 短 section 与相邻 section 合并
"""

import hashlib
import re
from typing import List, Optional

from app.core.config import settings
from app.services.chunking.chunker import BaseChunker, Chunk


class SmartChunker(BaseChunker):
    """智能切片器"""

    def __init__(
        self,
        max_chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        min_chunk_size: Optional[int] = None,
    ) -> None:
        """
        初始化切片器

        Args:
            max_chunk_size: 最大片段大小（token）
            overlap: 重叠大小（token）
            min_chunk_size: 最小片段大小（token）
        """
        self.max_chunk_size = max_chunk_size if max_chunk_size is not None else settings.CHUNK_SIZE
        self.overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP
        self.min_chunk_size = min_chunk_size if min_chunk_size is not None else settings.MIN_CHUNK_SIZE

    def chunk(self, text: str, document_id: str) -> List[Chunk]:
        """
        将文本切分为片段

        Args:
            text: 原始文本
            document_id: 文档 ID

        Returns:
            切片列表
        """
        # 尝试按标题切分
        sections = self._split_by_headers(text)

        if len(sections) <= 1:
            # 无标题或只有一个 section，回退到固定 Token 切片
            return self._chunk_fixed_size(text, document_id)

        # 处理每个 section
        chunks = []
        for section in sections:
            section_chunks = self._process_section(section, document_id)
            chunks.extend(section_chunks)

        # 合并短 section
        chunks = self._merge_short_chunks(chunks)

        # 重新编号
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.chunk_id = self._generate_chunk_id(document_id, i)

        return chunks

    def chunk_with_sections(self, text: str, document_id: str) -> List[Chunk]:
        """
        按章节切分文本

        Args:
            text: 原始文本
            document_id: 文档 ID

        Returns:
            切片列表
        """
        return self.chunk(text, document_id)

    def _split_by_headers(self, text: str) -> List[dict]:
        """
        按标题分割文本

        Args:
            text: 原始文本

        Returns:
            section 列表，每个 section 包含 title 和 content
        """
        # 匹配 # 或 ## 标题
        header_pattern = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)

        sections = []
        last_end = 0

        for match in header_pattern.finditer(text):
            # 如果标题前有内容，作为无标题 section
            if match.start() > last_end:
                content = text[last_end:match.start()].strip()
                if content:
                    sections.append({
                        "title": None,
                        "content": content,
                    })

            # 找到下一个标题的位置
            next_header = header_pattern.search(text, match.end())
            if next_header:
                end = next_header.start()
            else:
                end = len(text)

            content = text[match.start():end].strip()
            if content:
                sections.append({
                    "title": match.group(2).strip(),
                    "content": content,
                })

            last_end = end

        # 处理剩余内容
        if last_end < len(text):
            content = text[last_end:].strip()
            if content:
                sections.append({
                    "title": None,
                    "content": content,
                })

        return sections

    def _process_section(self, section: dict, document_id: str) -> List[Chunk]:
        """
        处理单个 section

        Args:
            section: section 信息
            document_id: 文档 ID

        Returns:
            切片列表
        """
        content = section["content"]
        title = section["title"]

        # 估算 token 数（粗略：1 token ≈ 4 字符）
        token_count = len(content) // 4

        if token_count <= self.max_chunk_size:
            # section 不需要二次切分
            return [Chunk(
                chunk_id="",
                content=content,
                chunk_index=0,
                start_offset=0,
                end_offset=len(content),
                section_title=title,
            )]
        else:
            # section 需要二次切分
            return self._chunk_fixed_size(
                content,
                document_id,
                section_title=title,
            )

    def _chunk_fixed_size(
        self,
        text: str,
        document_id: str,
        section_title: Optional[str] = None,
    ) -> List[Chunk]:
        """
        固定 Token 大小切片

        Args:
            text: 原始文本
            document_id: 文档 ID
            section_title: 章节标题

        Returns:
            切片列表
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # 计算结束位置
            end = start + self.max_chunk_size * 4  # 粗略估算

            # 如果不是最后一片，尝试在句子边界切分
            if end < len(text):
                # 寻找句子边界
                boundary = self._find_sentence_boundary(text, end)
                if boundary > start:
                    end = boundary

            # 提取内容
            content = text[start:end].strip()

            if content:
                chunks.append(Chunk(
                    chunk_id=self._generate_chunk_id(document_id, chunk_index),
                    content=content,
                    chunk_index=chunk_index,
                    start_offset=start,
                    end_offset=end,
                    section_title=section_title,
                ))
                chunk_index += 1

            # 移动到下一个位置（考虑 overlap）
            start = end - self.overlap * 4

        return chunks

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """
        寻找句子边界

        Args:
            text: 文本
            position: 起始位置

        Returns:
            句子边界位置
        """
        # 向后寻找句子结束符
        for i in range(position, min(position + 100, len(text))):
            if text[i] in "。！？\n":
                return i + 1

        # 向前寻找句子结束符
        for i in range(position, max(position - 100, 0), -1):
            if text[i] in "。！？\n":
                return i + 1

        return position

    def _merge_short_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        合并短切片

        Args:
            chunks: 原始切片列表

        Returns:
            合并后的切片列表
        """
        if not chunks:
            return chunks

        merged = []
        current = chunks[0]

        for next_chunk in chunks[1:]:
            # 估算当前 chunk 的 token 数
            current_tokens = len(current.content) // 4
            next_tokens = len(next_chunk.content) // 4

            if current_tokens < self.min_chunk_size:
                # 当前 chunk 太短，与下一个合并
                current = Chunk(
                    chunk_id=current.chunk_id,
                    content=current.content + "\n\n" + next_chunk.content,
                    chunk_index=current.chunk_index,
                    start_offset=current.start_offset,
                    end_offset=next_chunk.end_offset,
                    section_title=current.section_title or next_chunk.section_title,
                )
            else:
                merged.append(current)
                current = next_chunk

        merged.append(current)

        return merged

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """
        生成 chunk ID

        Args:
            document_id: 文档 ID
            chunk_index: 切片索引

        Returns:
            唯一的 chunk ID
        """
        content = f"{document_id}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
