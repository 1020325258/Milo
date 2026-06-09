## 新增需求

### 需求：生成文本向量

系统 SHALL 使用 DashScope text-embedding-v3 模型为文本片段生成向量嵌入。

#### 场景：单个片段向量化

- **WHEN** 文本片段被处理
- **THEN** 系统通过 DashScope API 生成 1536 维的向量嵌入

#### 场景：批量向量生成

- **WHEN** 多个片段被处理
- **THEN** 系统批量调用 API 以优化性能和成本

#### 场景：处理向量化 API 错误

- **WHEN** DashScope API 返回错误
- **THEN** 系统使用指数退避重试并记录失败日志

### 需求：在 Elasticsearch 中存储向量

系统 SHALL 将生成的向量嵌入存储在 Elasticsearch 的 dense_vector 字段中。

#### 场景：索引带向量的片段

- **WHEN** 片段向量被生成
- **THEN** 系统在 ES 中索引片段文档，包含文本、向量和元数据字段

#### 场景：更新现有片段向量

- **WHEN** 片段内容被更新
- **THEN** 系统重新生成向量并更新 ES 索引

#### 场景：删除片段向量

- **WHEN** 片段被删除
- **THEN** 系统从 ES 索引中删除片段文档

### 需求：配置 ES 向量索引

系统 SHALL 使用适当的向量搜索设置配置 ES 索引。

#### 场景：创建向量索引

- **WHEN** ES 索引被初始化
- **THEN** 系统创建具有 dense_vector 映射的索引（dims=1536, similarity=cosine）

#### 场景：配置 HNSW 参数

- **WHEN** ES 索引被创建
- **THEN** 系统配置 HNSW 索引参数：m=16, ef_construction=100

### 需求：支持增量索引

系统 SHALL 支持增量文档索引。

#### 场景：索引新文档

- **WHEN** 新文档被上传和处理
- **THEN** 系统索引所有片段而不影响现有文档

#### 场景：重新索引文档

- **WHEN** 文档被重新处理
- **THEN** 系统原子性地删除旧片段并索引新片段
