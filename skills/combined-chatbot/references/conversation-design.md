# Conversation Design Guide

## Table of Contents
- [Intent Design](#intent-design)
- [Entity Extraction](#entity-extraction)
- [Slot Filling](#slot-filling)
- [Dialogue Patterns](#dialogue-patterns)
- [Error Handling](#error-handling)

## Intent Design

### Intent Hierarchy

Organize intents in a hierarchy for maintainability:

```yaml
intents:
  booking:
    - book_appointment
    - cancel_appointment
    - reschedule_appointment
  information:
    - get_hours
    - get_location
    - get_pricing
  support:
    - report_issue
    - track_ticket
    - speak_to_human
  meta:
    - greeting
    - goodbye
    - help
    - fallback
```

### Intent Naming Conventions

- Use `verb_noun` format: `book_appointment`, `check_status`
- Keep names action-oriented and specific
- Avoid overlapping intents; each should have a clear purpose

### Intent Training Examples

Provide diverse examples for each intent:

```yaml
book_appointment:
  examples:
    - "I'd like to schedule an appointment"
    - "Can I book a meeting for next week?"
    - "Set up a consultation"
    - "I need to see someone about..."
    - "Book me in for Tuesday"
```

## Entity Extraction

### Common Entity Types

| Entity | Description | Examples |
|--------|-------------|----------|
| DATE | Calendar dates | "tomorrow", "next Monday", "March 15" |
| TIME | Time of day | "3pm", "afternoon", "9:30" |
| DURATION | Time spans | "30 minutes", "an hour" |
| PERSON | Names | "John Smith", "Dr. Wilson" |
| LOCATION | Places | "downtown office", "room 204" |
| NUMBER | Quantities | "two", "5", "a dozen" |

### Entity Extraction Patterns

**Regex-based (simple entities):**
```python
PHONE_PATTERN = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
EMAIL_PATTERN = r'\b[\w.-]+@[\w.-]+\.\w+\b'
```

**LLM-based (complex entities):**
```python
async def extract_entities(text: str, intent: str) -> dict:
    prompt = f"""Extract entities from this message for intent '{intent}':
    Message: {text}
    Return JSON with extracted entities."""
    return await llm.complete(prompt)
```

## Slot Filling

### Required vs Optional Slots

Define which slots are required for each intent:

```python
INTENT_SLOTS = {
    "book_appointment": {
        "required": ["date", "time", "service_type"],
        "optional": ["preferred_staff", "notes"]
    },
    "check_status": {
        "required": ["order_id"],
        "optional": []
    }
}
```

### Progressive Slot Collection

Collect missing slots naturally through conversation:

```python
async def collect_slots(context: ConversationContext, intent: str) -> Response:
    slots_config = INTENT_SLOTS[intent]
    missing = context.needs_clarification(slots_config["required"])

    if not missing:
        return await execute_intent(context)

    # Ask for next missing slot
    slot = missing[0]
    return Response(
        text=SLOT_PROMPTS[slot],
        expecting=slot
    )

SLOT_PROMPTS = {
    "date": "What date would you like?",
    "time": "What time works best for you?",
    "service_type": "What type of service do you need?",
}
```

### Slot Confirmation

Confirm critical slots before proceeding:

```python
def build_confirmation(context: ConversationContext) -> str:
    return f"""Let me confirm your appointment:
- Date: {context.slots['date']}
- Time: {context.slots['time']}
- Service: {context.slots['service_type']}

Is this correct?"""
```

## Dialogue Patterns

### Linear Flow

Simple sequential conversations:

```
User: "Book appointment"
Bot:  "What date?"
User: "Tomorrow"
Bot:  "What time?"
User: "3pm"
Bot:  "Confirmed for tomorrow at 3pm"
```

### Branching Flow

Different paths based on user input:

```python
async def handle_support_request(context):
    issue_type = context.slots.get("issue_type")

    if issue_type == "billing":
        return await handle_billing_issue(context)
    elif issue_type == "technical":
        return await handle_technical_issue(context)
    else:
        return await clarify_issue_type(context)
```

### Contextual Responses

Adapt responses based on conversation history:

```python
def get_greeting(context: ConversationContext) -> str:
    if context.is_returning_user:
        return f"Welcome back, {context.user_name}!"
    elif context.time_of_day == "morning":
        return "Good morning! How can I help?"
    else:
        return "Hello! How can I help you today?"
```

### Interruption Handling

Allow users to change topics mid-conversation:

```python
async def handle_message(message, context):
    new_intent = await classify_intent(message.text)

    # Check if user is interrupting current flow
    if context.current_intent and new_intent != context.current_intent:
        if new_intent in HIGH_PRIORITY_INTENTS:
            # Switch immediately
            context.save_state()  # Save for potential return
            return await handle_intent(new_intent, context)
        else:
            # Ask for confirmation
            return Response(
                text=f"We were discussing {context.current_intent}. "
                     f"Would you like to switch to {new_intent}?"
            )
```

## Error Handling

### Graceful Fallbacks

Handle unrecognized inputs smoothly:

```python
FALLBACK_RESPONSES = [
    "I'm not sure I understood that. Could you rephrase?",
    "I didn't catch that. Can you try saying it differently?",
    "I'm still learning! Could you be more specific?",
]

async def handle_fallback(context: ConversationContext) -> Response:
    context.fallback_count += 1

    if context.fallback_count >= 3:
        return Response(
            text="I'm having trouble understanding. "
                 "Would you like to speak with a human?",
            actions=[Action("connect_human"), Action("try_again")]
        )

    return Response(text=random.choice(FALLBACK_RESPONSES))
```

### Input Validation

Validate extracted entities:

```python
def validate_date(date_str: str) -> tuple[bool, str]:
    try:
        date = parse_date(date_str)
        if date < datetime.now():
            return False, "Please choose a future date."
        if date.weekday() >= 5:
            return False, "We're only open on weekdays."
        return True, ""
    except ValueError:
        return False, "I couldn't understand that date. Try 'tomorrow' or 'March 15'."
```

### Recovery Strategies

Help users recover from errors:

```python
async def handle_validation_error(context, slot, error_message):
    context.validation_attempts[slot] += 1

    if context.validation_attempts[slot] >= 2:
        # Offer alternatives
        suggestions = get_suggestions_for_slot(slot)
        return Response(
            text=f"{error_message}\n\nHere are some options:",
            actions=[Action(s) for s in suggestions]
        )

    return Response(text=error_message)
```
