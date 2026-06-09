# Milo 开发者指南

## 项目结构

```
milo/
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic Schema
│   │   ├── services/        # 业务服务
│   │   └── tests/           # 测试
│   ├── alembic/             # 数据库迁移
│   ├── pyproject.toml       # 项目配置
│   └── requirements.txt     # 依赖
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── components/      # 组件
│   │   ├── hooks/           # Hooks
│   │   ├── lib/             # 工具库
│   │   ├── pages/           # 页面
│   │   ├── stores/          # 状态管理
│   │   └── types/           # 类型定义
│   ├── package.json
│   └── vite.config.ts
├── docs/                     # 文档
├── scripts/                  # 脚本
└── openspec/                 # OpenSpec 提案
```

## 技术栈

### 后端

- **框架**: FastAPI
- **数据库**: MySQL 8.x + SQLAlchemy
- **搜索引擎**: Elasticsearch 8.x
- **AI 服务**: DashScope (Embedding + Rerank + LLM)
- **Agent 框架**: agentscope

### 前端

- **框架**: React 19 + TypeScript
- **构建工具**: Vite
- **UI 组件**: shadcn/ui + Tailwind CSS
- **状态管理**: Zustand
- **路由**: React Router

## 开发环境

### 前置条件

- Python 3.10+
- Node.js 18+
- MySQL 8.x
- Elasticsearch 8.x
- DashScope API Key

### 安装依赖

```bash
# 后端
cd backend
pip install -e ".[dev]"

# 前端
cd frontend
npm install
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入配置
```

### 初始化数据库

```bash
python scripts/init_database.py
python scripts/init_elasticsearch.py
```

### 启动服务

```bash
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
```

## 开发规范

### 代码风格

- **Python**: 使用 Black + isort + ruff
- **TypeScript**: 使用 ESLint + Prettier

```bash
# Python
black .
isort .
ruff check --fix .

# TypeScript
npm run lint
```

### 测试

```bash
# Python 测试
cd backend
pytest

# 带覆盖率
pytest --cov=app --cov-report=html
```

### Git 提交规范

使用 Conventional Commits:

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

## 架构设计

### 后端架构

```
API Layer (FastAPI Routes)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database (MySQL + Elasticsearch)
```

### 前端架构

```
Pages (Route Components)
    ↓
Components (UI Components)
    ↓
Stores (Zustand State)
    ↓
API Client (Fetch)
```

### 数据流

1. **文档处理流程**:
   ```
   Upload → Parse → Chunk → Embed → Index
   ```

2. **检索流程**:
   ```
   Query → Embed → Hybrid Search → Rerank → Response
   ```

## 扩展指南

### 添加新的文档类型

1. 在 `app/services/document/` 创建新解析器
2. 继承 `BaseParser` 类
3. 实现 `parse()` 和 `supported_extensions()` 方法
4. 在 `DocumentService` 中注册新解析器

### 添加新的 Embedding 模型

1. 在 `app/services/embedding/` 创建新服务
2. 继承 `BaseEmbeddingService` 类
3. 实现 `embed_texts()` 和 `embed_query()` 方法
4. 在 `deps.py` 中配置依赖注入

### 添加新的 API 端点

1. 在 `app/api/` 创建新路由文件
2. 定义路由和处理函数
3. 在 `app/main.py` 中注册路由
4. 添加相应的 Schema 和 Service

## 部署

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 生产环境配置

1. 设置 `APP_ENV=production`
2. 配置正式的数据库和 ES 连接
3. 设置安全的 API Key
4. 配置 HTTPS
5. 设置日志级别

## 故障排查

### 常见问题

1. **数据库连接失败**: 检查 MySQL 服务和连接配置
2. **ES 连接失败**: 检查 ES 服务和索引配置
3. **Embedding 失败**: 检查 DashScope API Key
4. **文档处理失败**: 检查文件格式和权限

### 日志查看

```bash
# 后端日志
tail -f logs/app.log

# ES 日志
docker logs elasticsearch
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request
5. 等待代码审查
