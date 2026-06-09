# Milo API 文档

## 概述

Milo 知识库 Agent 提供 RESTful API，支持知识库管理、文档管理、智能对话等功能。

**基础 URL**: `http://localhost:8000/api`

**API 文档**: `http://localhost:8000/docs` (Swagger UI)

## 知识库管理

### 创建知识库

**POST** `/knowledge/`

请求体:
```json
{
  "name": "知识库名称",
  "description": "知识库描述",
  "embedding_model": "text-embedding-v3"
}
```

响应: `201 Created`
```json
{
  "id": 1,
  "name": "知识库名称",
  "description": "知识库描述",
  "embedding_model": "text-embedding-v3",
  "document_count": 0,
  "chunk_count": 0,
  "created_at": "2026-06-09T10:00:00",
  "updated_at": "2026-06-09T10:00:00"
}
```

### 列出知识库

**GET** `/knowledge/`

参数:
- `page` (int): 页码，默认 1
- `page_size` (int): 每页数量，默认 10
- `search` (string): 搜索关键词

响应: `200 OK`
```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

### 获取知识库详情

**GET** `/knowledge/{id}`

响应: `200 OK`

### 更新知识库

**PUT** `/knowledge/{id}`

请求体:
```json
{
  "name": "新名称",
  "description": "新描述"
}
```

### 删除知识库

**DELETE** `/knowledge/{id}`

响应: `204 No Content`

### 获取知识库统计

**GET** `/knowledge/{id}/stats`

响应:
```json
{
  "document_count": 10,
  "chunk_count": 150
}
```

## 文档管理

### 上传文档

**POST** `/document/upload`

请求: `multipart/form-data`
- `file`: 文件（支持 .md, .pdf）
- `knowledge_base_id`: 知识库 ID

响应: `201 Created`

### 处理文档

**POST** `/document/{id}/process`

触发文档的解析、切片、向量化流程。

### 列出文档

**GET** `/document/`

参数:
- `knowledge_base_id` (int, 必填): 知识库 ID
- `page` (int): 页码
- `page_size` (int): 每页数量

### 删除文档

**DELETE** `/document/{id}`

## 对话

### 发送消息

**POST** `/chat/`

请求体:
```json
{
  "message": "用户问题",
  "conversation_id": null,
  "knowledge_base_id": null,
  "stream": false
}
```

响应:
```json
{
  "conversation_id": 1,
  "message": {
    "id": 2,
    "role": "assistant",
    "content": "回答内容",
    "references": {
      "items": [
        {
          "index": 1,
          "chunk_id": "xxx",
          "document_id": 1,
          "content": "引用内容",
          "relevance_score": 0.95
        }
      ]
    },
    "created_at": "2026-06-09T10:00:00"
  }
}
```

### 流式对话

**POST** `/chat/stream`

请求体同上，返回 `text/plain` 流式响应。

### 列出对话

**GET** `/chat/conversations`

参数:
- `page` (int): 页码
- `page_size` (int): 每页数量
- `search` (string): 搜索关键词

### 获取对话消息

**GET** `/chat/conversations/{id}/messages`

参数:
- `limit` (int): 消息数量限制

### 删除对话

**DELETE** `/chat/conversations/{id}`

## 健康检查

### 基本检查

**GET** `/health`

响应:
```json
{
  "status": "ok",
  "service": "milo"
}
```

### 详细检查

**GET** `/health/detailed`

响应:
```json
{
  "status": "ok",
  "service": "milo",
  "components": {
    "database": {"status": "ok"},
    "elasticsearch": {"status": "ok", "cluster_status": "green"}
  }
}
```

## 错误响应

所有错误响应格式:
```json
{
  "detail": "错误信息"
}
```

常见状态码:
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
