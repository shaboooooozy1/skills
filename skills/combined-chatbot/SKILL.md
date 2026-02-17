---
name: combined-chatbot
description: Guide for building conversational AI chatbots with natural language understanding, multi-turn dialogue, and platform integrations. Use when creating chatbots for customer service, virtual assistants, or interactive applications across platforms like Slack, Discord, Telegram, or custom web interfaces.
license: Complete terms in LICENSE.txt
---

# Chatbot Development Guide

Build conversational AI chatbots with robust dialogue management, context handling, and platform integrations.

## High-Level Workflow

### Phase 1: Design Conversation Flow

#### 1.1 Define Chatbot Purpose

Establish clear boundaries:
- **Primary use cases**: What problems does the chatbot solve?
- **User personas**: Who will interact with the chatbot?
- **Scope limitations**: What the chatbot explicitly does NOT handle

#### 1.2 Map Conversation Patterns

Design dialogue flows for each use case:
- **Intents**: User goals (e.g., `book_appointment`, `check_status`, `get_help`)
- **Entities**: Key information to extract (dates, names, product IDs)
- **Slots**: Required information to complete a task
- **Fallbacks**: Graceful handling of unrecognized inputs

See [Conversation Design Guide](./references/conversation-design.md) for patterns and examples.

### Phase 2: Choose Architecture

#### 2.1 Select Framework

**Python (Recommended for AI-heavy chatbots):**
- LangChain/LangGraph for complex conversational agents
- FastAPI for webhook endpoints
- Redis for session state management

**Node.js/TypeScript (Recommended for real-time chat):**
- Express or Fastify for webhook endpoints
- Socket.io for real-time messaging
- Better ecosystem for Slack/Discord SDKs

#### 2.2 Select State Management

Choose based on conversation complexity:

| Approach | Use When |
|----------|----------|
| Stateless | Simple Q&A, no context needed |
| Session-based | Multi-turn with short memory |
| Persistent | Long-running conversations, user history |

### Phase 3: Implementation

#### 3.1 Project Structure

```
chatbot/
├── src/
│   ├── handlers/        # Message handlers by intent
│   ├── services/        # Business logic, API integrations
│   ├── state/           # Conversation state management
│   ├── platforms/       # Platform-specific adapters
│   └── utils/           # Shared utilities
├── tests/
│   ├── unit/
│   └── conversations/   # Conversation flow tests
├── config/
│   └── intents.yaml     # Intent definitions
└── scripts/
    └── init_chatbot.py  # Project initialization
```

#### 3.2 Core Components

**Message Handler Pattern:**
```python
async def handle_message(message: Message, context: ConversationContext) -> Response:
    # 1. Extract intent and entities
    intent = await classify_intent(message.text)
    entities = await extract_entities(message.text, intent)

    # 2. Update conversation state
    context.update(intent=intent, entities=entities)

    # 3. Execute intent handler
    handler = get_handler(intent)
    response = await handler.execute(context)

    # 4. Return response with suggested actions
    return response
```

**Context Management:**
```python
class ConversationContext:
    user_id: str
    session_id: str
    history: list[Message]
    slots: dict[str, Any]
    current_intent: str | None

    def needs_clarification(self, required_slots: list[str]) -> list[str]:
        return [s for s in required_slots if s not in self.slots]
```

#### 3.3 Platform Integration

See [Platform Integration Guide](./references/platform-integrations.md) for platform-specific setup:
- Slack: Bolt SDK, slash commands, interactive components
- Discord: discord.py/discord.js, slash commands, buttons
- Telegram: python-telegram-bot, inline keyboards
- Web: WebSocket or REST API patterns

### Phase 4: Testing

#### 4.1 Conversation Testing

Test complete conversation flows, not just individual messages:

```python
def test_appointment_booking():
    bot = ChatBot()

    # Multi-turn conversation test
    assert bot.send("I want to book an appointment").contains("what date")
    assert bot.send("tomorrow at 3pm").contains("confirmed")
    assert bot.context.slots["date"] == "tomorrow"
    assert bot.context.slots["time"] == "3pm"
```

#### 4.2 Edge Cases

Test these scenarios:
- Interruptions mid-flow (user changes topic)
- Invalid inputs and graceful recovery
- Session timeout handling
- Concurrent conversations

See [Testing Patterns](./references/testing-patterns.md) for comprehensive test strategies.

### Phase 5: Deployment

#### 5.1 Webhook Setup

Most platforms use webhooks for message delivery:
1. Deploy chatbot to publicly accessible endpoint
2. Register webhook URL with platform
3. Verify webhook signature for security

#### 5.2 Scaling Considerations

- Use async handlers for I/O operations
- Implement rate limiting for API calls
- Store conversation state externally (Redis, database)
- Add health check endpoints

## Reference Files

- [Conversation Design Guide](./references/conversation-design.md) - Intent mapping, slot filling, dialogue patterns
- [Platform Integration Guide](./references/platform-integrations.md) - Platform-specific setup and best practices
- [Testing Patterns](./references/testing-patterns.md) - Conversation testing strategies

## Quick Start

Initialize a new chatbot project:
```bash
python scripts/init_chatbot.py my-chatbot --platform slack --language python
```
