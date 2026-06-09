## 背景

Milo 是一个基于 agentscope 框架的知识库 Agent 系统，旨在帮助 SRE 团队快速检索和利用历史工单和业务规则文档。当前系统需要依赖人工记忆和手动搜索来解决问题，效率低下且知识传承困难。

**技术环境**：
- 本地已有 MySQL 8.x 和 Elasticsearch 8.x 服务
- 有 DashScope API 访问权限（LLM + Embedding）
- 工单数据为 MD 格式，业务规则为 PDF 格式
- 参考项目：LightRAG（切片策略）、agentscope（Agent 框架）

**约束条件**：
- 不实现知识图谱功能（参考 LightRAG 理念但不实现图谱）
- 仅支持 MD 和 PDF 文件格式
- 不支持多模态能力

## 目标 / 非目标

**目标**:
- 实现完整的文档处理流水线：解析 → 切片 → 向量化 → 存储
- 提供高质量的混合检索能力（向量 + 全文 + Rerank）
- 构建基于 agentscope 的 RAG Agent，支持引用溯源
- 提供用户友好的 Web 界面
- 预留扩展接口（Skill、Data Query）

**非目标**:
- 不实现知识图谱和实体关系提取
- 不支持多模态文档（图片、音视频）
- 不实现实时协作编辑
- 不实现复杂的权限管理系统

## 技术决策

### 1. 文档解析方案

**选择**: PyMuPDF (PDF) + markdown-it-py (MD)

**理由**:
- PyMuPDF 是 Python 生态中最成熟的 PDF 解析库，支持文本提取、布局分析
- markdown-it-py 是 Markdown 的标准解析器，支持扩展语法
- 两者都是纯 Python 实现，无额外系统依赖

**替代方案**:
- PDFPlumber: 更适合表格提取，但文本布局分析不如 PyMuPDF
- pdf2image + OCR: 支持扫描件，但复杂度高且本需求不需要

### 2. 切片策略

**选择**: 固定 Token 切片（chunk_size=500, overlap=50）

**理由**:
- 参考 LightRAG 的默认策略，成熟稳定
- Token 数量可控，便于向量化和检索
- 重叠窗口保证上下文连续性
- 实现简单，性能优异

**替代方案**:
- 递归字符切片：更智能但实现复杂
- 语义切片：效果更好但需要额外 Embedding 调用，成本高

### 3. 向量化方案

**选择**: DashScope text-embedding-v3 + Elasticsearch dense_vector

**理由**:
- DashScope 与 LLM 同一供应商，统一管理
- ES 8.x 原生支持向量检索，无需额外向量数据库
- 支持混合检索（向量 + 全文），架构简化
- 用户已有 DashScope API Key

**替代方案**:
- 本地 Embedding 模型：需要 GPU 资源
- 独立向量数据库（Milvus/Qdrant）：增加运维复杂度

### 4. 检索策略

**选择**: 混合检索 + Rerank

**理由**:
- 向量检索捕获语义相似性
- BM25 全文检索捕获关键词匹配
- RRF 融合算法平衡两者权重
- Rerank 模型进一步提升相关性

**实现细节**:
- ES RRF (Reciprocal Rank Fusion) 融合向量和 BM25 结果
- 使用 DashScope 或本地 Rerank 模型精排
- Top-K 结果用于 LLM 上下文

### 5. Agent 框架

**选择**: agentscope ReAct Agent

**理由**:
- 阿里巴巴开源，与 DashScope 生态契合
- 支持工具注册、中间件、事件流
- 社区活跃，文档完善
- 用户已有 agentscope 项目经验

**替代方案**:
- LangChain：更流行但较重
- LlamaIndex：专注 RAG 但灵活性不足

### 6. 前端技术栈

**选择**: React 19 + TypeScript + Vite + shadcn/ui

**理由**:
- 与 agentscope web_ui 保持一致
- shadcn/ui 组件美观且可定制
- TypeScript 提供类型安全
- Vite 构建速度快

**替代方案**:
- Vue 3 + Element Plus：更轻量但生态不如 React
- Next.js：全栈框架但本项目不需要 SSR

### 7. 数据存储架构

**选择**: MySQL (元数据) + Elasticsearch (索引)

**理由**:
- MySQL 存储结构化数据：知识库、文档、对话历史
- ES 存储向量和全文索引：切片内容、Embedding
- 职责分离，各取所长

**数据模型**:
- MySQL: knowledge_base, document, chunk, conversation, message
- ES: chunks index (text + vector + metadata)

## 风险与权衡

### 风险 1: ES 向量检索性能

**风险**: 大规模向量检索可能性能不佳

**缓解措施**:
- 使用 ES 的 HNSW 索引算法
- 合理设置 Top-K 值（默认 20）
- 监控检索延迟，必要时优化索引参数

### 风险 2: Embedding 模型成本

**风险**: DashScope Embedding API 调用成本

**缓解措施**:
- 批量处理文档，减少 API 调用次数
- 缓存已向量化的切片
- 考虑本地 Embedding 模型作为备选

### 风险 3: 检索质量

**风险**: 混合检索 + Rerank 可能仍有相关性问题

**缓解措施**:
- 优化切片策略（chunk_size、overlap）
- 调整 RRF 权重参数
- 收集用户反馈持续优化

### 风险 4: agentscope 学习曲线

**风险**: 团队对 agentscope 不熟悉

**缓解措施**:
- 参考 agentscope 示例项目
- 先实现简单功能，逐步扩展
- 完善文档和注释

### 权衡 1: 简单性 vs 灵活性

**选择**: 优先简单性

**影响**: 固定切片策略可能不如语义切片灵活，但实现和维护成本低

### 权衡 2: 成本 vs 效果

**选择**: 使用云端 API

**影响**: 有 API 调用成本，但无需维护本地模型，效果有保障

## 迁移计划

这是全新项目，无迁移需求。

**部署步骤**:
1. 初始化 MySQL 和 ES 数据库/索引
2. 部署后端 FastAPI 服务
3. 部署前端 React 应用
4. 配置 DashScope API Key
5. 上传初始文档进行测试

**回滚策略**:
- 保留旧版本部署配置
- 数据库使用独立实例，可快速切换
- 前端支持版本回退

## 待解决问题

1. **Rerank 模型选择**: 使用 DashScope Rerank API 还是本地模型？
2. **对话历史保留策略**: 是否需要定期清理历史对话？
3. **多知识库隔离**: 不同知识库之间的检索是否需要隔离？
4. **并发处理能力**: 需要支持多少并发用户？
