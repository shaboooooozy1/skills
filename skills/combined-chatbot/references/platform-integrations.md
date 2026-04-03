# Platform Integration Guide

## Table of Contents
- [Slack](#slack)
- [Discord](#discord)
- [Telegram](#telegram)
- [Web Interface](#web-interface)
- [Common Patterns](#common-patterns)

## Slack

### Setup with Bolt SDK

**Python:**
```python
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.event("app_mention")
async def handle_mention(event, say):
    user_id = event["user"]
    text = event["text"]
    response = await chatbot.process(text, user_id=user_id)
    await say(response.text, blocks=response.blocks)

@app.event("message")
async def handle_dm(event, say):
    if event.get("channel_type") == "im":
        response = await chatbot.process(event["text"], user_id=event["user"])
        await say(response.text)

# Start with Socket Mode for development
handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
handler.start()
```

**Node.js:**
```javascript
const { App } = require('@slack/bolt');

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET
});

app.event('app_mention', async ({ event, say }) => {
  const response = await chatbot.process(event.text, event.user);
  await say({ text: response.text, blocks: response.blocks });
});

app.start(3000);
```

### Slash Commands

```python
@app.command("/ask")
async def handle_ask(ack, command, respond):
    await ack()  # Acknowledge within 3 seconds
    response = await chatbot.process(command["text"], user_id=command["user_id"])
    await respond(response.text)
```

### Interactive Components

```python
@app.action("confirm_booking")
async def handle_confirm(ack, body, respond):
    await ack()
    user_id = body["user"]["id"]
    context = get_context(user_id)
    result = await complete_booking(context)
    await respond(f"Booking confirmed: {result.confirmation_id}")

def build_confirmation_blocks(context):
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Confirm booking for {context.slots['date']}?*"}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Confirm"}, "action_id": "confirm_booking", "style": "primary"},
            {"type": "button", "text": {"type": "plain_text", "text": "Cancel"}, "action_id": "cancel_booking"}
        ]}
    ]
```

## Discord

### Setup with discord.py

```python
import discord
from discord import app_commands

class ChatBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"Logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Respond to DMs or mentions
        if isinstance(message.channel, discord.DMChannel) or self.user in message.mentions:
            response = await chatbot.process(message.content, user_id=str(message.author.id))
            await message.channel.send(response.text)

client = ChatBot()

@client.tree.command(name="ask", description="Ask the chatbot a question")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    response = await chatbot.process(question, user_id=str(interaction.user.id))
    await interaction.followup.send(response.text)

client.run(os.environ["DISCORD_TOKEN"])
```

### Buttons and Select Menus

```python
class ConfirmView(discord.ui.View):
    def __init__(self, context):
        super().__init__(timeout=180)
        self.context = context

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.primary)
    async def confirm(self, interaction, button):
        result = await complete_booking(self.context)
        await interaction.response.send_message(f"Confirmed: {result.confirmation_id}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.send_message("Cancelled.")

# Usage
view = ConfirmView(context)
await channel.send("Confirm your booking?", view=view)
```

## Telegram

### Setup with python-telegram-bot

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

async def start(update: Update, context):
    await update.message.reply_text("Hello! How can I help you today?")

async def handle_message(update: Update, context):
    user_id = str(update.effective_user.id)
    response = await chatbot.process(update.message.text, user_id=user_id)

    if response.buttons:
        keyboard = [[InlineKeyboardButton(b.text, callback_data=b.action)] for b in response.buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(response.text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(response.text)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    response = await chatbot.process_action(query.data, user_id=str(query.from_user.id))
    await query.edit_message_text(response.text)

app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()
```

### Inline Keyboards

```python
def build_options_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"select_{opt}")] for opt in options]
    return InlineKeyboardMarkup(keyboard)

# Usage
keyboard = build_options_keyboard(["Option A", "Option B", "Option C"])
await update.message.reply_text("Please choose:", reply_markup=keyboard)
```

## Web Interface

### REST API Pattern

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class MessageRequest(BaseModel):
    text: str
    session_id: str
    user_id: str | None = None

class MessageResponse(BaseModel):
    text: str
    actions: list[dict] = []
    session_id: str

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    context = await get_or_create_context(request.session_id, request.user_id)
    response = await chatbot.process(request.text, context=context)
    return MessageResponse(
        text=response.text,
        actions=[a.to_dict() for a in response.actions],
        session_id=request.session_id
    )

@app.post("/action")
async def handle_action(session_id: str, action: str):
    context = await get_context(session_id)
    response = await chatbot.process_action(action, context=context)
    return MessageResponse(text=response.text, session_id=session_id)
```

### WebSocket Pattern

```python
from fastapi import WebSocket

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    context = await get_or_create_context(session_id)

    try:
        while True:
            data = await websocket.receive_json()
            response = await chatbot.process(data["text"], context=context)
            await websocket.send_json({
                "text": response.text,
                "actions": [a.to_dict() for a in response.actions]
            })
    except WebSocketDisconnect:
        await save_context(context)
```

### Frontend Integration

```javascript
// React hook for chat
function useChat(sessionId) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (text) => {
    setMessages(prev => [...prev, { role: 'user', text }]);
    setIsLoading(true);

    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, session_id: sessionId })
    });

    const data = await response.json();
    setMessages(prev => [...prev, { role: 'assistant', text: data.text, actions: data.actions }]);
    setIsLoading(false);
  };

  return { messages, sendMessage, isLoading };
}
```

## Common Patterns

### Platform Adapter Interface

Create a unified interface for multi-platform support:

```python
from abc import ABC, abstractmethod

class PlatformAdapter(ABC):
    @abstractmethod
    async def send_message(self, channel_id: str, text: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def send_buttons(self, channel_id: str, text: str, buttons: list) -> None:
        pass

    @abstractmethod
    def parse_message(self, raw_event: dict) -> Message:
        pass

class SlackAdapter(PlatformAdapter):
    def __init__(self, client):
        self.client = client

    async def send_message(self, channel_id, text, **kwargs):
        await self.client.chat_postMessage(channel=channel_id, text=text, **kwargs)

class DiscordAdapter(PlatformAdapter):
    # ... implementation
```

### Webhook Signature Verification

Always verify webhook signatures:

```python
import hmac
import hashlib

def verify_slack_signature(request_body: bytes, timestamp: str, signature: str, secret: str) -> bool:
    base = f"v0:{timestamp}:{request_body.decode()}"
    computed = "v0=" + hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)

@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    if not verify_slack_signature(body, timestamp, signature, SLACK_SIGNING_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process event...
```

### Rate Limiting

Implement rate limiting for API calls:

```python
from asyncio import Semaphore
from functools import wraps

class RateLimiter:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)

    def limit(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.semaphore:
                return await func(*args, **kwargs)
        return wrapper

limiter = RateLimiter(max_concurrent=5)

@limiter.limit
async def call_external_api(data):
    # API call here
    pass
```
