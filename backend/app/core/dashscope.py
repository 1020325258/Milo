"""
DashScope API 客户端

提供 DashScope API 的封装，支持 Embedding、Rerank 和 LLM 功能。
支持 qwen 模型的 thinking 功能。
支持通过 OpenAI 兼容 API 调用新模型（如 qwen3.7-plus）。
"""

from typing import List, Optional, AsyncGenerator, Tuple

import dashscope
from dashscope import TextEmbedding, TextReRank, Generation
from dashscope.api_entities.dashscope_response import GenerationResponse
from openai import OpenAI

from app.core.config import settings


class DashScopeClient:
    """DashScope API 客户端"""

    def __init__(self) -> None:
        """初始化客户端"""
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        # OpenAI 兼容客户端（用于新模型如 qwen3.7-plus）
        self._openai_client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def embed_texts(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表
            model: 模型名称，默认使用配置中的模型

        Returns:
            向量列表
        """
        model = model or settings.EMBEDDING_MODEL

        response = TextEmbedding.call(
            model=model,
            input=texts,
        )

        if response.status_code != 200:
            raise Exception(f"Embedding API 错误: {response.code} - {response.message}")

        return [item["embedding"] for item in response.output["embeddings"]]

    def rerank_texts(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[dict]:
        """
        文本重排序

        Args:
            query: 查询文本
            documents: 候选文档列表
            top_n: 返回前 N 个结果
            model: 模型名称

        Returns:
            排序结果列表，包含 index 和 relevance_score
        """
        top_n = top_n or settings.RERANK_TOP_K

        response = TextReRank.call(
            model="gte-rerank",
            query=query,
            documents=documents,
            top_n=top_n,
            return_documents=True,
        )

        if response.status_code != 200:
            raise Exception(f"Rerank API 错误: {response.code} - {response.message}")

        return response.output["results"]

    async def chat_stream_with_thinking(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        流式对话生成，支持 thinking 内容

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            (content, thinking_content) 元组
        """
        model = model or settings.LLM_MODEL
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        # 检查是否使用 OpenAI 兼容 API
        if self._use_openai_compatible(model):
            async for content, thinking in self._openai_chat_stream_with_thinking(
                messages, model, temperature, max_tokens
            ):
                yield content, thinking
        else:
            # 检查模型是否支持 thinking
            supports_thinking = self._model_supports_thinking(model)

            if supports_thinking:
                async for content, thinking in self._dashscope_chat_stream_with_thinking(
                    messages, model, temperature, max_tokens
                ):
                    yield content, thinking
            else:
                async for content in self._dashscope_chat_stream(
                    messages, model, temperature, max_tokens
                ):
                    yield content, None

    async def chat_stream(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话生成（不返回 thinking 内容）

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            流式响应内容
        """
        async for content, _ in self.chat_stream_with_thinking(
            messages, model, temperature, max_tokens
        ):
            if content:
                yield content

    def _model_supports_thinking(self, model: str) -> bool:
        """
        检查模型是否支持 thinking 功能

        Args:
            model: 模型名称

        Returns:
            是否支持 thinking
        """
        # 支持 thinking 的模型列表
        thinking_models = [
            "qwen-plus",
            "qwen-max",
            "qwen-turbo",
            "qwen-long",
            "qwen-vl-plus",
            "qwen-vl-max",
            "qwen3.",
            "qwq",
            "qwq-plus",
            "qwq-32b",
            "deepseek-r1",
            "deepseek-r1-distill",
        ]

        model_lower = model.lower()
        for thinking_model in thinking_models:
            if thinking_model in model_lower:
                return True
        return False

    def _use_openai_compatible(self, model: str) -> bool:
        """
        检查模型是否需要使用 OpenAI 兼容 API

        Args:
            model: 模型名称

        Returns:
            是否使用 OpenAI 兼容 API
        """
        # 需要使用 OpenAI 兼容 API 的模型
        openai_models = ["qwen3."]
        model_lower = model.lower()
        for m in openai_models:
            if m in model_lower:
                return True
        return False

    async def _openai_chat_stream_with_thinking(
        self,
        messages: List[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        OpenAI 兼容 API 流式对话，支持 thinking 内容
        用于 qwen3.7-plus 等新模型

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            (content, thinking_content) 元组
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _stream_worker():
            try:
                response = self._openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    extra_body={"enable_thinking": True},
                )

                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        content = ""
                        thinking = ""

                        if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                            thinking = delta.reasoning_content
                        if hasattr(delta, "content") and delta.content:
                            content = delta.content

                        if content or thinking:
                            loop.call_soon_threadsafe(queue.put_nowait, (content, thinking))

                loop.call_soon_threadsafe(queue.put_nowait, None)  # 结束标记
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, Exception(f"LLM API 错误: {str(e)}"))

        # 在线程池中运行阻塞的流式调用
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(_stream_worker)

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            executor.shutdown(wait=False)

    async def _dashscope_chat_stream_with_thinking(
        self,
        messages: List[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        DashScope 流式对话，支持 thinking 内容

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            (content, thinking_content) 元组
        """
        responses = Generation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            incremental_output=True,
            enable_thinking=True,
            result_format="message",
        )

        for response in responses:
            if response.status_code == 200:
                choices = response.output.get("choices")
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    thinking = message.get("reasoning_content", "")
                    yield content, thinking
            else:
                raise Exception(f"LLM API 错误: {response.code} - {response.message}")

    async def _dashscope_chat_stream(
        self,
        messages: List[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """
        DashScope 流式对话（不支持 thinking）

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            流式响应内容
        """
        responses = Generation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            incremental_output=True,
        )

        for response in responses:
            if response.status_code == 200:
                choices = response.output.get("choices")
                if choices and len(choices) > 0:
                    content = choices[0].get("message", {}).get("content", "")
                    if content:
                        yield content
            else:
                raise Exception(f"LLM API 错误: {response.code} - {response.message}")


# 创建全局客户端实例
dashscope_client = DashScopeClient()
