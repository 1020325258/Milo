## ADDED Requirements

### Requirement: Perform vector similarity search
The system SHALL search for similar chunks using vector cosine similarity.

#### Scenario: Semantic search
- **WHEN** user query is converted to embedding
- **THEN** system searches ES with KNN query returning top-K most similar chunks

#### Scenario: Filter by knowledge base
- **WHEN** user specifies knowledge base
- **THEN** system filters search results to specified knowledge base only

#### Scenario: Filter by document
- **WHEN** user specifies document
- **THEN** system filters search results to specified document only

### Requirement: Perform BM25 full-text search
The system SHALL search for chunks using BM25 text matching.

#### Scenario: Keyword search
- **WHEN** user query is processed
- **THEN** system searches ES with match query returning relevant chunks by text similarity

#### Scenario: Handle Chinese text
- **WHEN** query contains Chinese characters
- **THEN** system uses appropriate Chinese analyzer for tokenization

### Requirement: Fuse retrieval results with RRF
The system SHALL combine vector and BM25 results using Reciprocal Rank Fusion.

#### Scenario: RRF fusion
- **WHEN** vector and BM25 results are retrieved
- **THEN** system combines results using RRF algorithm with configurable k parameter (default=60)

#### Scenario: Weighted fusion
- **WHEN** fusion is performed
- **THEN** system applies configurable weights to vector and BM25 scores

### Requirement: Support configurable retrieval parameters
The system SHALL allow configuration of retrieval behavior.

#### Scenario: Custom top-K
- **WHEN** user specifies top_k parameter
- **THEN** system returns specified number of results

#### Scenario: Custom similarity threshold
- **WHEN** user specifies similarity_threshold parameter
- **THEN** system filters results below threshold
