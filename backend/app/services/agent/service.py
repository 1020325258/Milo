"""
Agent 服务

提供基于 agentscope 的 RAG Agent 功能。
参考 LightRAG 的设计，实现动态 token 分配和引用系统。
"""

import json
from typing import AsyncGenerator, List, Optional

from app.core.config import settings
from app.core.dashscope import dashscope_client
from app.services.embedding.base import BaseEmbeddingService
from app.services.retrieval.reranker import RerankResult
from app.services.retrieval.retriever import Retriever


class AgentService:
    """Agent 服务"""

    def __init__(
        self,
        retriever: Retriever,
        embedding: BaseEmbeddingService,
    ) -> None:
        """
        初始化服务

        Args:
            retriever: 检索服务
            embedding: Embedding 服务
        """
        self.retriever = retriever
        self.embedding = embedding

    async def chat(
        self,
        message: str,
        knowledge_base_id: Optional[int] = None,
        conversation_history: Optional[List[dict]] = None,
        doc_names: Optional[dict] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        流式对话

        Args:
            message: 用户消息
            knowledge_base_id: 知识库 ID
            conversation_history: 对话历史
            doc_names: 文档 ID 到文件名的映射

        Yields:
            流式响应字典，包含 content 和 thinking_content
        """
        # 检索相关文档
        results = self.retriever.retrieve(
            query=message,
            knowledge_base_id=str(knowledge_base_id) if knowledge_base_id else None,
            top_k=settings.RETRIEVAL_TOP_K,
            use_rerank=False,  # 暂时禁用 Rerank
        )

        # 处理 chunks，生成引用列表
        processed_chunks, reference_list = self._process_chunks(results)

        # 构建上下文
        context = self._build_context(processed_chunks, reference_list, doc_names=doc_names)

        # 构建消息列表
        messages = self._build_messages(message, context, conversation_history)

        # 流式调用 LLM
        async for content, thinking in dashscope_client.chat_stream_with_thinking(messages):
            yield {
                "content": content,
                "thinking_content": thinking,
            }

    def _process_chunks(
        self, results: List[RerankResult]
    ) -> tuple[List[dict], List[dict]]:
        """
        处理 chunks，生成引用列表

        参考 LightRAG 的 generate_reference_list_from_chunks 函数

        Args:
            results: 检索结果

        Returns:
            (processed_chunks, reference_list)
        """
        if not results:
            return [], []

        # 1. 提取所有有效的 document_id 并统计出现次数
        doc_id_counts = {}
        for result in results:
            doc_id = result.document_id
            if doc_id:
                doc_id_counts[doc_id] = doc_id_counts.get(doc_id, 0) + 1

        # 2. 按出现频率排序，然后按首次出现顺序
        doc_id_with_indices = []
        seen_doc_ids = set()
        for i, result in enumerate(results):
            doc_id = result.document_id
            if doc_id and doc_id not in seen_doc_ids:
                doc_id_with_indices.append(
                    (doc_id, doc_id_counts[doc_id], i)
                )
                seen_doc_ids.add(doc_id)

        # 按频率降序排序，然后按首次出现索引升序排序
        sorted_doc_ids = sorted(
            doc_id_with_indices, key=lambda x: (-x[1], x[2])
        )
        unique_doc_ids = [item[0] for item in sorted_doc_ids]

        # 3. 创建 doc_id 到 reference_id 的映射
        doc_id_to_ref_id = {}
        for i, doc_id in enumerate(unique_doc_ids):
            doc_id_to_ref_id[doc_id] = str(i + 1)

        # 4. 为每个 chunk 添加 reference_id
        processed_chunks = []
        for result in results:
            chunk = {
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "knowledge_base_id": result.knowledge_base_id,
                "content": result.content,
                "metadata": result.metadata,
                "original_score": result.original_score,
                "rerank_score": result.rerank_score,
                "reference_id": doc_id_to_ref_id.get(result.document_id, ""),
            }
            processed_chunks.append(chunk)

        # 5. 构建 reference_list
        reference_list = []
        for i, doc_id in enumerate(unique_doc_ids):
            reference_list.append(
                {
                    "reference_id": str(i + 1),
                    "document_id": doc_id,
                }
            )

        return processed_chunks, reference_list

    def _build_context(
        self,
        processed_chunks: List[dict],
        reference_list: List[dict],
        doc_names: Optional[dict] = None,
    ) -> str:
        """
        构建检索上下文

        参考 LightRAG 的 naive_query_context 模板

        Args:
            processed_chunks: 处理后的 chunks
            reference_list: 引用列表

        Returns:
            上下文文本
        """
        if not processed_chunks:
            return ""

        # 构建 chunks 上下文
        chunks_context = []
        for chunk in processed_chunks:
            chunks_context.append(
                {
                    "reference_id": chunk["reference_id"],
                    "content": chunk["content"],
                }
            )

        text_units_str = "\n".join(
            json.dumps(chunk, ensure_ascii=False) for chunk in chunks_context
        )

        # 构建引用列表
        doc_names = doc_names or {}
        ref_lines = []
        for ref in reference_list:
            if ref["reference_id"]:
                doc_id = ref["document_id"]
                doc_label = doc_names.get(doc_id, f"文档 {doc_id}")
                ref_lines.append(f"[{ref['reference_id']}] {doc_label}")
        reference_list_str = "\n".join(ref_lines)

        # 使用 LightRAG 风格的上下文模板
        context_template = """Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```
{reference_list_str}
```

"""

        return context_template.format(
            text_chunks_str=text_units_str,
            reference_list_str=reference_list_str,
        )

    def _build_messages(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> List[dict]:
        """
        构建消息列表

        参考 LightRAG 的 naive_rag_response 模板

        Args:
            query: 用户查询
            context: 检索上下文
            conversation_history: 对话历史

        Returns:
            消息列表
        """
        # 使用 LightRAG 风格的系统提示
        system_prompt = """---Role---

你是一个专业的 AI 助手，专门从提供的知识库中综合信息。你的主要功能是仅使用提供的**上下文**中的信息准确回答用户查询。

---Goal---

生成全面、结构良好的答案来回答用户查询。
答案必须整合在**上下文**中找到的文档块中的相关事实。
如果提供了对话历史，请考虑以保持对话流畅性并避免重复信息。

---Instructions---

1. 逐步指导：
  - 仔细确定用户查询在对话历史背景下的意图，以完全理解用户的信息需求。
  - 仔细检查**上下文**中的文档块。识别并提取所有与回答用户查询直接相关的信息。
  - 将提取的事实编织成连贯、逻辑的响应。你自己的知识必须仅用于构建流畅的句子和连接想法，而不是引入任何外部信息。
  - **关键**：跟踪每个事实来自哪个 reference_id，在正文中用 `[n]` 标记引用来源。例如："客户可以通过发起合同变更来修改手机号[1]。"

2. 引用规范（参考 LightRAG）：
  - 在每个事实、数据点或结论后立即插入 `[n]` 标记
  - `[n]` 对应参考文档列表中的 reference_id
  - 多个来源支持同一事实时：`[1][2]`
  - 引用标记紧跟在相关文字之后，无需空格：`签约手机号需要变更[1]`
  - 不要在回答末尾添加参考文献列表，系统会自动处理

3. 内容和依据：
  - 严格遵守**上下文**中提供的上下文；不要发明、假设或推断任何未明确说明的信息。
  - 如果在**上下文**中找不到答案，请说明没有足够的信息来回答。不要尝试猜测。

4. 格式和语言：
  - 响应必须使用与用户查询相同的语言。
  - 响应必须使用 Markdown 格式以增强清晰度和结构（例如，标题、粗体文本、要点）。

---Context---

{content_data}
"""

        # 格式化系统提示
        sys_prompt = system_prompt.format(content_data=context)

        # 构建消息列表
        messages = [{"role": "system", "content": sys_prompt}]

        # 添加对话历史
        if conversation_history:
            # 保留最近 3 轮对话
            for msg in conversation_history[-6:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # 添加用户查询
        messages.append({"role": "user", "content": query})

        return messages

    def _generate_response(
        self,
        prompt: str,
        processed_chunks: List[dict],
        reference_list: List[dict],
    ) -> str:
        """
        生成响应（非流式）

        Args:
            prompt: 完整的 Prompt
            processed_chunks: 处理后的 chunks
            reference_list: 引用列表

        Returns:
            生成的响应
        """
        # 简单实现：返回检索结果的摘要
        # 实际应调用 LLM（如 agentscope）
        if not processed_chunks:
            return "抱歉，没有找到相关的文档内容。"

        response_parts = ["根据知识库中的文档，我找到了以下相关信息：\n"]

        # 按引用 ID 分组
        ref_groups = {}
        for chunk in processed_chunks:
            ref_id = chunk["reference_id"]
            if ref_id not in ref_groups:
                ref_groups[ref_id] = []
            ref_groups[ref_id].append(chunk)

        # 为每个引用生成摘要
        for ref_id in sorted(ref_groups.keys(), key=lambda x: int(x)):
            chunks = ref_groups[ref_id]
            # 使用第一个 chunk 作为摘要
            content = chunks[0]["content"]
            # 截取前 200 字符作为摘要
            if len(content) > 200:
                content = content[:200] + "..."

            response_parts.append(f"[{ref_id}] {content}\n")

        # 添加参考文献部分
        response_parts.append("\n### References\n")
        for ref in reference_list:
            if ref["reference_id"]:
                response_parts.append(
                    f"- [{ref['reference_id']}] 文档 {ref['document_id']}"
                )

        return "\n".join(response_parts)

    def build_references(
        self,
        results: List[RerankResult],
        doc_names: Optional[dict] = None,
    ) -> List[dict]:
        """
        构建引用列表

        Args:
            results: 检索结果
            doc_names: 文档 ID 到文件名的映射（可选）

        Returns:
            引用列表
        """
        doc_names = doc_names or {}

        # 处理 chunks，生成引用列表
        processed_chunks, reference_list = self._process_chunks(results)

        # 构建引用
        references = []
        for ref in reference_list:
            if ref["reference_id"]:
                # 找到对应的 chunks
                ref_chunks = [
                    c for c in processed_chunks
                    if c["reference_id"] == ref["reference_id"]
                ]
                if ref_chunks:
                    # 使用第一个 chunk 的内容作为引用
                    content = ref_chunks[0]["content"]
                    if len(content) > 500:
                        content = content[:500] + "..."

                    doc_id = ref["document_id"]
                    document_name = doc_names.get(doc_id, f"文档 {doc_id}")

                    references.append(
                        {
                            "index": int(ref["reference_id"]),
                            "chunk_id": ref_chunks[0]["chunk_id"],
                            "document_id": doc_id,
                            "document_name": document_name,
                            "content": content,
                            "relevance_score": ref_chunks[0].get(
                                "rerank_score", 0
                            ),
                        }
                    )

        return references
