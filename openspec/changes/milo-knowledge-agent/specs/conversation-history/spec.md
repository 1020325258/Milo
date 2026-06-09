## ADDED Requirements

### Requirement: Store conversation history
The system SHALL store all conversation history in MySQL.

#### Scenario: Create new conversation
- **WHEN** user starts new chat
- **THEN** system creates conversation record with unique ID and timestamp

#### Scenario: Store messages
- **WHEN** user or agent sends message
- **THEN** system stores message with role, content, and timestamp

#### Scenario: Store retrieval context
- **WHEN** agent retrieves context for answer
- **THEN** system stores retrieved chunk IDs with message

### Requirement: List conversation history
The system SHALL allow users to view conversation history.

#### Scenario: List conversations
- **WHEN** user requests conversation list
- **THEN** system returns paginated list sorted by last activity time

#### Scenario: Search conversations
- **WHEN** user provides search keyword
- **THEN** system returns conversations matching keyword in messages

### Requirement: View conversation details
The system SHALL allow users to view conversation details.

#### Scenario: View conversation messages
- **WHEN** user selects conversation
- **THEN** system displays all messages in chronological order

#### Scenario: View message citations
- **WHEN** user views agent message with citations
- **THEN** system displays citations with links to source chunks

### Requirement: Delete conversation history
The system SHALL allow users to delete conversation history.

#### Scenario: Delete single conversation
- **WHEN** user deletes conversation
- **THEN** system removes conversation and all associated messages

#### Scenario: Bulk delete conversations
- **WHEN** user selects multiple conversations for deletion
- **THEN** system removes all selected conversations

### Requirement: Support conversation context window
The system SHALL manage conversation context for multi-turn dialogue.

#### Scenario: Maintain context in conversation
- **WHEN** user asks follow-up question
- **THEN** agent uses conversation history for context

#### Scenario: Context window limit
- **WHEN** conversation exceeds context window limit
- **THEN** system summarizes or truncates older messages
