## ADDED Requirements

### Requirement: Generate text embeddings
The system SHALL generate vector embeddings for text chunks using DashScope text-embedding-v3 model.

#### Scenario: Single chunk embedding
- **WHEN** text chunk is processed
- **THEN** system generates 1536-dimensional vector embedding via DashScope API

#### Scenario: Batch embedding generation
- **WHEN** multiple chunks are processed
- **THEN** system batches API calls to optimize performance and cost

#### Scenario: Handle embedding API errors
- **WHEN** DashScope API returns error
- **THEN** system retries with exponential backoff and logs failures

### Requirement: Store vectors in Elasticsearch
The system SHALL store generated embeddings in Elasticsearch dense_vector field.

#### Scenario: Index chunk with vector
- **WHEN** chunk embedding is generated
- **THEN** system indexes chunk document in ES with text, vector, and metadata fields

#### Scenario: Update existing chunk vector
- **WHEN** chunk content is updated
- **THEN** system regenerates embedding and updates ES index

#### Scenario: Delete chunk vector
- **WHEN** chunk is deleted
- **THEN** system removes chunk document from ES index

### Requirement: Configure ES vector index
The system SHALL configure ES index with appropriate vector search settings.

#### Scenario: Create vector index
- **WHEN** ES index is initialized
- **THEN** system creates index with dense_vector mapping (dims=1536, similarity=cosine)

#### Scenario: Configure HNSW parameters
- **WHEN** ES index is created
- **THEN** system configures HNSW index with m=16, ef_construction=100

### Requirement: Support incremental indexing
The system SHALL support incremental document indexing.

#### Scenario: Index new document
- **WHEN** new document is uploaded and processed
- **THEN** system indexes all chunks without affecting existing documents

#### Scenario: Re-index document
- **WHEN** document is re-processed
- **THEN** system deletes old chunks and indexes new chunks atomically
