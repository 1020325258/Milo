## Why

当前 SRE 团队在处理合同签约相关问题时，需要手动查阅大量的工单历史和业务规则文档，效率低下且知识传承困难。需要一个智能化的知识库助手，能够基于历史工单和业务规则快速提供准确的解决方案，提升问题处理效率和一致性。

## What Changes

- 新增完整的知识库管理系统，支持 MD 和 PDF 文档的上传、解析、切片和向量化
- 实现基于 Elasticsearch 的混合检索能力（向量相似度 + BM25 全文检索）
- 集成 Rerank 模型提升检索结果质量
- 基于 agentscope 框架构建 RAG Agent，支持引用溯源和原文查看
- 提供现代化的 Web 前端界面，支持知识库管理、文档管理和智能对话
- 预留 Skill 系统和数据查询接口，支持后续功能扩展

## Capabilities

### New Capabilities

- `document-parsing`: 文档解析能力，支持 MD 和 PDF 格式的文档解析为纯文本
- `text-chunking`: 文本切片能力，基于固定 Token 策略进行智能切片，支持重叠窗口
- `vector-indexing`: 向量索引能力，集成 DashScope Embedding 模型，将文本转换为向量并存储到 Elasticsearch
- `hybrid-retrieval`: 混合检索能力，结合向量相似度和 BM25 全文检索，通过 RRF 算法融合排序
- `reranking`: 重排序能力，集成 Rerank 模型对检索结果进行精排，提升相关性
- `rag-agent`: RAG Agent 能力，基于 agentscope 构建智能问答 Agent，支持引用溯源
- `knowledge-management`: 知识库管理能力，支持多知识库的创建、编辑和删除
- `conversation-history`: 对话历史能力，记录和管理用户的多轮对话

### Modified Capabilities

（无，这是全新项目）

## Impact

- **新增依赖**: agentscope, FastAPI, SQLAlchemy, PyMuPDF, markdown-it-py, elasticsearch-py, dashscope
- **基础设施**: 需要 MySQL 8.x 和 Elasticsearch 8.x 服务
- **API 接口**: 新增知识库管理、文档管理、对话交互等 RESTful API
- **前端应用**: 新增 React 前端应用，提供用户交互界面
- **数据存储**: MySQL 存储元数据，Elasticsearch 存储向量和全文索引
