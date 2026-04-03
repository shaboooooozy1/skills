# Chatbot Testing Patterns

## Table of Contents
- [Conversation Testing](#conversation-testing)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Edge Case Testing](#edge-case-testing)
- [Evaluation Framework](#evaluation-framework)

## Conversation Testing

### Conversation Test Framework

Test complete dialogue flows, not just individual responses:

```python
import pytest
from chatbot import ChatBot
from chatbot.testing import ConversationTest

class TestBookingFlow:
    @pytest.fixture
    def bot(self):
        return ChatBot(test_mode=True)

    def test_complete_booking(self, bot):
        conv = ConversationTest(bot)

        # Start booking
        response = conv.send("I want to book an appointment")
        assert "date" in response.text.lower()
        assert conv.context.current_intent == "book_appointment"

        # Provide date
        response = conv.send("tomorrow")
        assert "time" in response.text.lower()
        assert conv.context.slots["date"] == "tomorrow"

        # Provide time
        response = conv.send("3pm")
        assert "confirm" in response.text.lower()
        assert conv.context.slots["time"] == "3pm"

        # Confirm
        response = conv.send("yes")
        assert "confirmed" in response.text.lower()
        assert conv.context.booking_id is not None

    def test_booking_cancellation_midflow(self, bot):
        conv = ConversationTest(bot)

        conv.send("Book an appointment")
        conv.send("tomorrow")

        # User cancels mid-flow
        response = conv.send("cancel")
        assert "cancelled" in response.text.lower()
        assert conv.context.current_intent is None
```

### Conversation Test Helper

```python
class ConversationTest:
    def __init__(self, bot: ChatBot):
        self.bot = bot
        self.context = ConversationContext(
            user_id="test_user",
            session_id="test_session"
        )
        self.history = []

    def send(self, text: str) -> Response:
        message = Message(text=text, user_id=self.context.user_id)
        self.history.append(("user", text))
        response = self.bot.process_sync(message, self.context)
        self.history.append(("bot", response.text))
        return response

    def assert_slot(self, slot: str, value: str):
        assert self.context.slots.get(slot) == value, \
            f"Expected slot '{slot}' to be '{value}', got '{self.context.slots.get(slot)}'"

    def assert_intent(self, intent: str):
        assert self.context.current_intent == intent, \
            f"Expected intent '{intent}', got '{self.context.current_intent}'"

    def print_history(self):
        for role, text in self.history:
            print(f"{role.upper()}: {text}")
```

### Parameterized Conversation Tests

Test multiple variations efficiently:

```python
@pytest.mark.parametrize("date_input,expected_date", [
    ("tomorrow", "tomorrow"),
    ("next Monday", "next Monday"),
    ("March 15", "March 15"),
    ("the 15th", "the 15th"),
])
def test_date_extraction(bot, date_input, expected_date):
    conv = ConversationTest(bot)
    conv.send("Book appointment")
    conv.send(date_input)
    assert conv.context.slots["date"] == expected_date
```

## Unit Testing

### Intent Classification Tests

```python
class TestIntentClassification:
    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    @pytest.mark.parametrize("input_text,expected_intent", [
        ("I want to book an appointment", "book_appointment"),
        ("Schedule a meeting", "book_appointment"),
        ("Cancel my reservation", "cancel_appointment"),
        ("What are your hours?", "get_hours"),
        ("Hello", "greeting"),
        ("asdfghjkl", "fallback"),
    ])
    def test_intent_classification(self, classifier, input_text, expected_intent):
        result = classifier.classify(input_text)
        assert result.intent == expected_intent

    def test_intent_confidence(self, classifier):
        result = classifier.classify("I want to book an appointment")
        assert result.confidence > 0.8
```

### Entity Extraction Tests

```python
class TestEntityExtraction:
    @pytest.fixture
    def extractor(self):
        return EntityExtractor()

    def test_date_extraction(self, extractor):
        entities = extractor.extract("Book for tomorrow at 3pm")
        assert entities["date"] == "tomorrow"
        assert entities["time"] == "3pm"

    def test_multiple_entities(self, extractor):
        entities = extractor.extract("Book with Dr. Smith on March 15 at 2:30pm")
        assert entities["person"] == "Dr. Smith"
        assert entities["date"] == "March 15"
        assert entities["time"] == "2:30pm"

    @pytest.mark.parametrize("input_text,expected_phone", [
        ("Call me at 555-123-4567", "555-123-4567"),
        ("My number is 5551234567", "5551234567"),
        ("Reach me at (555) 123-4567", "(555) 123-4567"),
    ])
    def test_phone_extraction(self, extractor, input_text, expected_phone):
        entities = extractor.extract(input_text)
        assert entities["phone"] == expected_phone
```

### Context Management Tests

```python
class TestConversationContext:
    def test_slot_filling(self):
        context = ConversationContext(user_id="test", session_id="test")
        context.update(slots={"date": "tomorrow"})
        assert context.slots["date"] == "tomorrow"

    def test_needs_clarification(self):
        context = ConversationContext(user_id="test", session_id="test")
        context.update(slots={"date": "tomorrow"})

        required = ["date", "time", "service_type"]
        missing = context.needs_clarification(required)

        assert "date" not in missing
        assert "time" in missing
        assert "service_type" in missing

    def test_history_management(self):
        context = ConversationContext(user_id="test", session_id="test")
        context.add_message(Message(text="Hello", role="user"))
        context.add_message(Message(text="Hi there!", role="assistant"))

        assert len(context.history) == 2
        assert context.history[-1].text == "Hi there!"
```

## Integration Testing

### Platform Integration Tests

```python
class TestSlackIntegration:
    @pytest.fixture
    def mock_slack_client(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_message_handling(self, mock_slack_client):
        adapter = SlackAdapter(mock_slack_client)

        event = {
            "type": "message",
            "text": "Hello",
            "user": "U123456",
            "channel": "C123456"
        }

        message = adapter.parse_message(event)
        assert message.text == "Hello"
        assert message.user_id == "U123456"

    @pytest.mark.asyncio
    async def test_response_formatting(self, mock_slack_client):
        adapter = SlackAdapter(mock_slack_client)

        response = Response(
            text="Choose an option:",
            buttons=[Button("Option A", "select_a"), Button("Option B", "select_b")]
        )

        blocks = adapter.format_response(response)
        assert len(blocks) == 2  # text + actions
        assert blocks[1]["type"] == "actions"
```

### End-to-End Tests

```python
@pytest.mark.e2e
class TestEndToEnd:
    @pytest.fixture
    def live_bot(self):
        # Use test credentials
        return ChatBot(config=TestConfig())

    @pytest.mark.asyncio
    async def test_full_booking_flow(self, live_bot):
        session_id = str(uuid.uuid4())

        # Make actual API calls
        response1 = await live_bot.process("Book appointment", session_id=session_id)
        assert response1.status == "success"

        response2 = await live_bot.process("Tomorrow at 3pm", session_id=session_id)
        assert "confirm" in response2.text.lower()

        response3 = await live_bot.process("Yes", session_id=session_id)
        assert "confirmed" in response3.text.lower()
```

## Edge Case Testing

### Interruption Handling

```python
class TestInterruptions:
    def test_topic_switch(self, bot):
        conv = ConversationTest(bot)

        # Start booking
        conv.send("Book an appointment")
        conv.send("tomorrow")

        # Switch to different topic
        response = conv.send("Actually, what are your hours?")

        # Should handle the switch gracefully
        assert "hours" in response.text.lower() or "would you like to" in response.text.lower()

    def test_return_to_previous_flow(self, bot):
        conv = ConversationTest(bot)

        conv.send("Book an appointment")
        conv.send("tomorrow")
        conv.send("What are your hours?")

        # Return to booking
        response = conv.send("Let's continue with the booking")
        assert "time" in response.text.lower()  # Should resume asking for time
```

### Error Recovery

```python
class TestErrorRecovery:
    def test_invalid_date(self, bot):
        conv = ConversationTest(bot)

        conv.send("Book an appointment")
        response = conv.send("yesterday")

        assert "future" in response.text.lower() or "valid" in response.text.lower()
        # Should still be in booking flow
        assert conv.context.current_intent == "book_appointment"

    def test_repeated_failures(self, bot):
        conv = ConversationTest(bot)

        conv.send("Book an appointment")
        conv.send("asdfgh")
        conv.send("qwerty")
        response = conv.send("zzzzz")

        # After multiple failures, should offer help
        assert "help" in response.text.lower() or "human" in response.text.lower()

    def test_empty_input(self, bot):
        conv = ConversationTest(bot)
        response = conv.send("")
        assert response.text  # Should have some response
```

### Session Management

```python
class TestSessionManagement:
    def test_session_timeout(self, bot):
        conv = ConversationTest(bot)

        conv.send("Book an appointment")
        conv.send("tomorrow")

        # Simulate timeout
        conv.context.last_activity = datetime.now() - timedelta(hours=1)

        response = conv.send("3pm")

        # Should start fresh or ask to continue
        assert "start" in response.text.lower() or "continue" in response.text.lower()

    def test_concurrent_sessions(self, bot):
        conv1 = ConversationTest(bot, session_id="session1")
        conv2 = ConversationTest(bot, session_id="session2")

        conv1.send("Book an appointment")
        conv2.send("What are your hours?")

        # Sessions should be independent
        assert conv1.context.current_intent == "book_appointment"
        assert conv2.context.current_intent == "get_hours"
```

## Evaluation Framework

### Automated Evaluation

```python
class ChatbotEvaluator:
    def __init__(self, bot: ChatBot, test_cases: list[dict]):
        self.bot = bot
        self.test_cases = test_cases
        self.results = []

    def run_evaluation(self) -> EvaluationReport:
        for case in self.test_cases:
            result = self._run_case(case)
            self.results.append(result)

        return EvaluationReport(
            total=len(self.results),
            passed=sum(1 for r in self.results if r.passed),
            failed=sum(1 for r in self.results if not r.passed),
            details=self.results
        )

    def _run_case(self, case: dict) -> TestResult:
        conv = ConversationTest(self.bot)

        for turn in case["turns"]:
            response = conv.send(turn["user"])

            if "expected_contains" in turn:
                if turn["expected_contains"].lower() not in response.text.lower():
                    return TestResult(
                        case_id=case["id"],
                        passed=False,
                        error=f"Expected '{turn['expected_contains']}' in response"
                    )

            if "expected_slot" in turn:
                slot, value = turn["expected_slot"]
                if conv.context.slots.get(slot) != value:
                    return TestResult(
                        case_id=case["id"],
                        passed=False,
                        error=f"Expected slot {slot}={value}"
                    )

        return TestResult(case_id=case["id"], passed=True)
```

### Test Case Definition

```yaml
# test_cases.yaml
test_cases:
  - id: booking_happy_path
    description: "Complete booking flow"
    turns:
      - user: "I want to book an appointment"
        expected_contains: "date"
      - user: "tomorrow"
        expected_slot: ["date", "tomorrow"]
        expected_contains: "time"
      - user: "3pm"
        expected_slot: ["time", "3pm"]
        expected_contains: "confirm"
      - user: "yes"
        expected_contains: "confirmed"

  - id: booking_with_interruption
    description: "Booking with topic change"
    turns:
      - user: "Book an appointment"
        expected_contains: "date"
      - user: "What are your hours?"
        expected_intent: "get_hours"
      - user: "Let's continue booking"
        expected_contains: "date"
```

### Metrics Collection

```python
class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(list)

    def record_conversation(self, conv: ConversationTest):
        self.metrics["turns"].append(len(conv.history) // 2)
        self.metrics["fallback_rate"].append(conv.context.fallback_count / max(1, len(conv.history) // 2))
        self.metrics["completion_rate"].append(1 if conv.context.task_completed else 0)

    def report(self) -> dict:
        return {
            "avg_turns": sum(self.metrics["turns"]) / len(self.metrics["turns"]),
            "avg_fallback_rate": sum(self.metrics["fallback_rate"]) / len(self.metrics["fallback_rate"]),
            "completion_rate": sum(self.metrics["completion_rate"]) / len(self.metrics["completion_rate"]),
        }
```
