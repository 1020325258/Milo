# Milo Backend

Milo 知识库 Agent 后端服务，基于 FastAPI 构建。

## 功能特性

- 文档解析（MD、PDF）
- 智能文本切片
- 向量化存储（DashScope Embedding + Elasticsearch）
- 混合检索（向量 + BM25 + RRF）
- Rerank 精排
- RAG Agent（agentscope）
- 对话历史管理

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入配置
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
isort .
ruff check --fix .
```

### 类型检查

```bash
mypy .
```
