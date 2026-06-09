## ADDED Requirements

### Requirement: Create knowledge base
The system SHALL allow users to create new knowledge bases.

#### Scenario: Create with name and description
- **WHEN** user provides name and description
- **THEN** system creates knowledge base with specified metadata

#### Scenario: Create with embedding model config
- **WHEN** user specifies embedding model
- **THEN** system creates knowledge base with specified embedding configuration

#### Scenario: Duplicate name check
- **WHEN** user creates knowledge base with existing name
- **THEN** system returns error indicating name already exists

### Requirement: Edit knowledge base
The system SHALL allow users to edit knowledge base metadata.

#### Scenario: Update name and description
- **WHEN** user updates name or description
- **THEN** system updates knowledge base metadata

#### Scenario: Update embedding config
- **WHEN** user updates embedding model configuration
- **THEN** system updates config and marks for re-indexing

### Requirement: Delete knowledge base
The system SHALL allow users to delete knowledge bases.

#### Scenario: Delete empty knowledge base
- **WHEN** user deletes knowledge base with no documents
- **THEN** system removes knowledge base immediately

#### Scenario: Delete knowledge base with documents
- **WHEN** user deletes knowledge base containing documents
- **THEN** system confirms deletion and removes all associated documents and chunks

### Requirement: List knowledge bases
The system SHALL allow users to list all knowledge bases.

#### Scenario: List with pagination
- **WHEN** user requests knowledge base list
- **THEN** system returns paginated list with total count

#### Scenario: List with search
- **WHEN** user provides search keyword
- **THEN** system returns knowledge bases matching keyword in name or description

### Requirement: View knowledge base details
The system SHALL allow users to view knowledge base details.

#### Scenario: View statistics
- **WHEN** user views knowledge base
- **THEN** system displays document count, chunk count, and storage size

#### Scenario: View recent documents
- **WHEN** user views knowledge base
- **THEN** system displays recently added documents
