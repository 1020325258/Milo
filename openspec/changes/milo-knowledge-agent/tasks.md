## 1. 项目初始化

- [ ] 1.1 创建项目目录结构（backend/frontend/docs/scripts）
- [ ] 1.2 初始化 Python 后端项目（pyproject.toml, requirements.txt）
- [ ] 1.3 初始化 React 前端项目（package.json, vite.config.ts）
- [ ] 1.4 配置开发环境（.env.example, .gitignore）
- [ ] 1.5 创建数据库迁移脚本（alembic）
- [ ] 1.6 创建 ES 索引初始化脚本

## 2. 后端核心配置

- [ ] 2.1 实现 FastAPI 应用工厂（app/main.py）
- [ ] 2.2 实现配置管理（app/core/config.py）
- [ ] 2.3 实现依赖注入（app/core/deps.py）
- [ ] 2.4 实现数据库连接和 Session 管理
- [ ] 2.5 实现 ES 客户端连接
- [ ] 2.6 实现 DashScope API 客户端

## 3. 数据模型层

- [ ] 3.1 实现 KnowledgeBase SQLAlchemy 模型
- [ ] 3.2 实现 Document SQLAlchemy 模型
- [ ] 3.3 实现 Chunk SQLAlchemy 模型
- [ ] 3.4 实现 Conversation SQLAlchemy 模型
- [ ] 3.5 实现 Message SQLAlchemy 模型
- [ ] 3.6 创建 Pydantic Schema（请求/响应模型）
- [ ] 3.7 实现数据库迁移脚本

## 4. 文档解析服务

- [ ] 4.1 实现文档解析器基类（app/services/document/parser.py）
- [ ] 4.2 实现 Markdown 解析器（app/services/document/md_parser.py）
- [ ] 4.3 实现 PDF 解析器（app/services/document/pdf_parser.py）
- [ ] 4.4 实现文档元数据提取
- [ ] 4.5 实现文件格式验证
- [ ] 4.6 编写文档解析单元测试

## 5. 文本切片服务

- [ ] 5.1 实现切片器基类（app/services/chunking/chunker.py）
- [ ] 5.2 实现固定 Token 切片器（app/services/chunking/token_chunker.py）
- [ ] 5.3 实现 chunk ID 生成逻辑
- [ ] 5.4 实现 chunk 元数据记录（位置、偏移量）
- [ ] 5.5 支持可配置切片参数（chunk_size, overlap）
- [ ] 5.6 编写切片服务单元测试

## 6. 向量化服务

- [ ] 6.1 实现 Embedding 服务基类（app/services/embedding/base.py）
- [ ] 6.2 实现 DashScope Embedding 服务（app/services/embedding/dashscope.py）
- [ ] 6.3 实现批量 Embedding 调用
- [ ] 6.4 实现 Embedding 缓存机制
- [ ] 6.5 实现错误重试和降级策略
- [ ] 6.6 编写向量化服务单元测试

## 7. Elasticsearch 服务

- [ ] 7.1 实现 ES 客户端封装（app/services/retrieval/es_client.py）
- [ ] 7.2 实现 ES 索引创建和配置（dense_vector mapping）
- [ ] 7.3 实现文档索引（index, update, delete）
- [ ] 7.4 实现向量检索（KNN query）
- [ ] 7.5 实现 BM25 全文检索
- [ ] 7.6 实现 RRF 混合检索融合
- [ ] 7.7 编写 ES 服务单元测试

## 8. Rerank 服务

- [ ] 8.1 实现 Rerank 服务基类（app/services/retrieval/reranker.py）
- [ ] 8.2 实现 DashScope Rerank 集成
- [ ] 8.3 实现本地 Rerank 模型支持（可选）
- [ ] 8.4 实现 Rerank 错误处理和降级
- [ ] 8.5 支持可配置 Rerank 参数
- [ ] 8.6 编写 Rerank 服务单元测试

## 9. 检索服务

- [ ] 9.1 实现检索器基类（app/services/retrieval/retriever.py）
- [ ] 9.2 实现混合检索流程（向量 + BM25 + Rerank）
- [ ] 9.3 实现知识库级别过滤
- [ ] 9.4 实现文档级别过滤
- [ ] 9.5 实现检索结果排序和截断
- [ ] 9.6 编写检索服务单元测试

## 10. 知识库管理服务

- [ ] 10.1 实现知识库 CRUD 服务（app/services/knowledge/）
- [ ] 10.2 实现知识库统计信息查询
- [ ] 10.3 实现知识库删除级联操作
- [ ] 10.4 实现知识库搜索功能
- [ ] 10.5 编写知识库管理单元测试

## 11. 文档管理服务

- [ ] 11.1 实现文档上传服务（app/services/document/）
- [ ] 11.2 实现文档处理流水线（解析 → 切片 → 向量化）
- [ ] 11.3 实现文档重新处理功能
- [ ] 11.4 实现文档删除和清理
- [ ] 11.5 实现文档列表和搜索
- [ ] 11.6 编写文档管理单元测试

## 12. Agent 服务

- [ ] 12.1 实现 agentscope Agent 初始化（app/services/agent/）
- [ ] 12.2 实现 RAG 工具注册
- [ ] 12.3 实现多查询生成策略
- [ ] 12.4 实现上下文组装和 Prompt 模板
- [ ] 12.5 实现引用溯源和原文关联
- [ ] 12.6 实现流式响应支持
- [ ] 12.7 编写 Agent 服务单元测试

## 13. 对话历史服务

- [ ] 13.1 实现对话 CRUD 服务（app/services/conversation/）
- [ ] 13.2 实现消息存储和查询
- [ ] 13.3 实现对话上下文窗口管理
- [ ] 13.4 实现对话搜索功能
- [ ] 13.5 实现对话批量删除
- [ ] 13.6 编写对话历史单元测试

## 14. API 路由层

- [ ] 14.1 实现知识库 API（app/api/knowledge.py）
- [ ] 14.2 实现文档 API（app/api/document.py）
- [ ] 14.3 实现对话 API（app/api/chat.py）
- [ ] 14.4 实现健康检查 API（app/api/health.py）
- [ ] 14.5 实现 API 错误处理中间件
- [ ] 14.6 实现 API 请求日志中间件
- [ ] 14.7 编写 API 集成测试

## 15. 前端基础框架

- [ ] 15.1 配置 Vite 和 TypeScript
- [ ] 15.2 配置 Tailwind CSS 和 shadcn/ui
- [ ] 15.3 实现路由配置（React Router）
- [ ] 15.4 实现 API 客户端封装
- [ ] 15.5 实现全局状态管理
- [ ] 15.6 实现通用组件（Layout, Header, Sidebar）

## 16. 前端知识库管理页面

- [ ] 16.1 实现知识库列表页面
- [ ] 16.2 实现知识库创建表单
- [ ] 16.3 实现知识库编辑表单
- [ ] 16.4 实现知识库详情页面
- [ ] 16.5 实现知识库删除确认

## 17. 前端文档管理页面

- [ ] 17.1 实现文档上传组件
- [ ] 17.2 实现文档列表页面
- [ ] 17.3 实现文档详情页面
- [ ] 17.4 实现文档删除确认
- [ ] 17.5 实现文档处理状态展示

## 18. 前端对话页面

- [ ] 18.1 实现聊天界面组件
- [ ] 18.2 实现消息列表展示
- [ ] 18.3 实现消息输入框
- [ ] 18.4 实现引用展示组件
- [ ] 18.5 实现原文查看弹窗
- [ ] 18.6 实现流式响应展示

## 19. 前端对话历史页面

- [ ] 19.1 实现对话历史列表
- [ ] 19.2 实现对话详情查看
- [ ] 19.3 实现对话搜索功能
- [ ] 19.4 实现对话删除功能

## 20. 集成测试和文档

- [ ] 20.1 编写端到端集成测试
- [ ] 20.2 性能测试和优化
- [ ] 20.3 编写 API 文档（OpenAPI）
- [ ] 20.4 编写用户使用文档
- [ ] 20.5 编写开发者文档
- [ ] 20.6 创建 Docker Compose 部署配置
