#!/usr/bin/env python3
"""Initialize a new chatbot project with recommended structure."""

import argparse
import os
from pathlib import Path

PLATFORMS = ["slack", "discord", "telegram", "web"]
LANGUAGES = ["python", "typescript"]


def create_python_project(project_path: Path, platform: str) -> None:
    """Create Python chatbot project structure."""
    dirs = [
        "src/handlers",
        "src/services",
        "src/state",
        "src/platforms",
        "src/utils",
        "tests/unit",
        "tests/conversations",
        "config",
    ]

    for dir_path in dirs:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Main entry point
    (project_path / "src" / "__init__.py").write_text("")
    (project_path / "src" / "main.py").write_text(
        f'''"""Main entry point for the chatbot."""

import os
from chatbot import ChatBot
from platforms.{platform} import {platform.title()}Adapter


def main():
    bot = ChatBot()
    adapter = {platform.title()}Adapter(bot)
    adapter.run()


if __name__ == "__main__":
    main()
'''
    )

    # Chatbot core
    (project_path / "src" / "chatbot.py").write_text(
        '''"""Core chatbot logic."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    text: str
    user_id: str
    channel_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Response:
    text: str
    buttons: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ConversationContext:
    user_id: str
    session_id: str
    history: list[Message] = field(default_factory=list)
    slots: dict[str, Any] = field(default_factory=dict)
    current_intent: str | None = None

    def needs_clarification(self, required_slots: list[str]) -> list[str]:
        return [s for s in required_slots if s not in self.slots]

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key == "slots":
                self.slots.update(value)
            else:
                setattr(self, key, value)


class ChatBot:
    def __init__(self):
        self.contexts: dict[str, ConversationContext] = {}

    def get_context(self, session_id: str, user_id: str) -> ConversationContext:
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                user_id=user_id,
                session_id=session_id
            )
        return self.contexts[session_id]

    async def process(self, text: str, session_id: str, user_id: str) -> Response:
        context = self.get_context(session_id, user_id)
        message = Message(text=text, user_id=user_id)
        context.history.append(message)

        # TODO: Implement intent classification
        # TODO: Implement entity extraction
        # TODO: Route to appropriate handler

        return Response(text=f"You said: {text}")
'''
    )

    # Platform adapter
    (project_path / "src" / "platforms" / "__init__.py").write_text("")
    (project_path / "src" / "platforms" / f"{platform}.py").write_text(
        get_platform_adapter(platform)
    )

    # Handlers
    (project_path / "src" / "handlers" / "__init__.py").write_text("")
    (project_path / "src" / "handlers" / "base.py").write_text(
        '''"""Base handler interface."""

from abc import ABC, abstractmethod
from chatbot import ConversationContext, Response


class BaseHandler(ABC):
    @abstractmethod
    async def execute(self, context: ConversationContext) -> Response:
        pass
'''
    )

    # Config
    (project_path / "config" / "intents.yaml").write_text(
        '''# Intent definitions
intents:
  greeting:
    examples:
      - "hello"
      - "hi"
      - "hey there"
  help:
    examples:
      - "help"
      - "what can you do"
      - "how does this work"
  fallback:
    examples: []
'''
    )

    # Requirements
    requirements = ["pydantic>=2.0", "pyyaml>=6.0"]
    if platform == "slack":
        requirements.extend(["slack-bolt>=1.18", "slack-sdk>=3.21"])
    elif platform == "discord":
        requirements.append("discord.py>=2.3")
    elif platform == "telegram":
        requirements.append("python-telegram-bot>=20.0")
    elif platform == "web":
        requirements.extend(["fastapi>=0.100", "uvicorn>=0.23"])

    (project_path / "requirements.txt").write_text("\n".join(requirements) + "\n")

    # Test file
    (project_path / "tests" / "__init__.py").write_text("")
    (project_path / "tests" / "conversations" / "__init__.py").write_text("")
    (project_path / "tests" / "conversations" / "test_basic.py").write_text(
        '''"""Basic conversation tests."""

import pytest
from src.chatbot import ChatBot, ConversationContext


class TestBasicConversation:
    @pytest.fixture
    def bot(self):
        return ChatBot()

    @pytest.mark.asyncio
    async def test_greeting(self, bot):
        response = await bot.process(
            "hello",
            session_id="test",
            user_id="user1"
        )
        assert response.text

    @pytest.mark.asyncio
    async def test_context_persistence(self, bot):
        await bot.process("hello", session_id="test", user_id="user1")
        context = bot.get_context("test", "user1")
        assert len(context.history) == 1
'''
    )


def get_platform_adapter(platform: str) -> str:
    """Get platform-specific adapter code."""
    adapters = {
        "slack": '''"""Slack platform adapter."""

import os
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from chatbot import ChatBot


class SlackAdapter:
    def __init__(self, bot: ChatBot):
        self.bot = bot
        self.app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
        self._register_handlers()

    def _register_handlers(self):
        @self.app.event("message")
        async def handle_message(event, say):
            if event.get("channel_type") == "im":
                response = await self.bot.process(
                    event["text"],
                    session_id=event["channel"],
                    user_id=event["user"]
                )
                await say(response.text)

        @self.app.event("app_mention")
        async def handle_mention(event, say):
            response = await self.bot.process(
                event["text"],
                session_id=event["channel"],
                user_id=event["user"]
            )
            await say(response.text)

    def run(self):
        import asyncio
        handler = AsyncSocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
        asyncio.run(handler.start_async())
''',
        "discord": '''"""Discord platform adapter."""

import os
import discord
from discord import app_commands
from chatbot import ChatBot


class DiscordAdapter(discord.Client):
    def __init__(self, bot: ChatBot):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.bot = bot
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"Logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if isinstance(message.channel, discord.DMChannel) or self.user in message.mentions:
            response = await self.bot.process(
                message.content,
                session_id=str(message.channel.id),
                user_id=str(message.author.id)
            )
            await message.channel.send(response.text)

    def run(self):
        super().run(os.environ["DISCORD_TOKEN"])
''',
        "telegram": '''"""Telegram platform adapter."""

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from chatbot import ChatBot


class TelegramAdapter:
    def __init__(self, bot: ChatBot):
        self.bot = bot
        self.app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).build()
        self._register_handlers()

    def _register_handlers(self):
        async def start(update: Update, context):
            await update.message.reply_text("Hello! How can I help you?")

        async def handle_message(update: Update, context):
            response = await self.bot.process(
                update.message.text,
                session_id=str(update.effective_chat.id),
                user_id=str(update.effective_user.id)
            )
            await update.message.reply_text(response.text)

        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    def run(self):
        self.app.run_polling()
''',
        "web": '''"""Web platform adapter using FastAPI."""

import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chatbot import ChatBot


class MessageRequest(BaseModel):
    text: str
    session_id: str | None = None
    user_id: str | None = None


class MessageResponse(BaseModel):
    text: str
    session_id: str
    buttons: list = []


class WebAdapter:
    def __init__(self, bot: ChatBot):
        self.bot = bot
        self.app = FastAPI(title="Chatbot API")
        self._register_routes()

    def _register_routes(self):
        @self.app.post("/chat", response_model=MessageResponse)
        async def chat(request: MessageRequest):
            session_id = request.session_id or str(uuid.uuid4())
            user_id = request.user_id or "anonymous"

            response = await self.bot.process(
                request.text,
                session_id=session_id,
                user_id=user_id
            )

            return MessageResponse(
                text=response.text,
                session_id=session_id,
                buttons=[b.__dict__ for b in response.buttons]
            )

        @self.app.get("/health")
        async def health():
            return {"status": "ok"}

    def run(self):
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
''',
    }
    return adapters.get(platform, adapters["web"])


def create_typescript_project(project_path: Path, platform: str) -> None:
    """Create TypeScript chatbot project structure."""
    dirs = [
        "src/handlers",
        "src/services",
        "src/state",
        "src/platforms",
        "src/utils",
        "tests",
        "config",
    ]

    for dir_path in dirs:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Package.json
    deps = {
        "slack": '"@slack/bolt": "^3.17.0"',
        "discord": '"discord.js": "^14.14.0"',
        "telegram": '"telegraf": "^4.15.0"',
        "web": '"express": "^4.18.0"',
    }

    (project_path / "package.json").write_text(
        f'''{{
  "name": "{project_path.name}",
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "build": "tsc",
    "start": "node dist/main.js",
    "dev": "ts-node src/main.ts",
    "test": "jest"
  }},
  "dependencies": {{
    {deps.get(platform, deps["web"])}
  }},
  "devDependencies": {{
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "ts-node": "^10.9.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0"
  }}
}}
'''
    )

    # tsconfig.json
    (project_path / "tsconfig.json").write_text(
        '''{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
'''
    )

    # Main chatbot types and class
    (project_path / "src" / "chatbot.ts").write_text(
        '''export interface Message {
  text: string;
  userId: string;
  channelId?: string;
  metadata?: Record<string, unknown>;
}

export interface Response {
  text: string;
  buttons?: Array<{ label: string; action: string }>;
  metadata?: Record<string, unknown>;
}

export interface ConversationContext {
  userId: string;
  sessionId: string;
  history: Message[];
  slots: Record<string, unknown>;
  currentIntent?: string;
}

export class ChatBot {
  private contexts: Map<string, ConversationContext> = new Map();

  getContext(sessionId: string, userId: string): ConversationContext {
    if (!this.contexts.has(sessionId)) {
      this.contexts.set(sessionId, {
        userId,
        sessionId,
        history: [],
        slots: {},
      });
    }
    return this.contexts.get(sessionId)!;
  }

  async process(text: string, sessionId: string, userId: string): Promise<Response> {
    const context = this.getContext(sessionId, userId);
    context.history.push({ text, userId });

    // TODO: Implement intent classification
    // TODO: Implement entity extraction
    // TODO: Route to appropriate handler

    return { text: `You said: ${text}` };
  }
}
'''
    )

    # Main entry point
    (project_path / "src" / "main.ts").write_text(
        f'''import {{ ChatBot }} from "./chatbot.js";

const bot = new ChatBot();

// TODO: Initialize {platform} adapter and start
console.log("Chatbot starting...");
'''
    )


def main():
    parser = argparse.ArgumentParser(description="Initialize a new chatbot project")
    parser.add_argument("name", help="Project name")
    parser.add_argument(
        "--platform",
        choices=PLATFORMS,
        default="web",
        help="Target platform (default: web)",
    )
    parser.add_argument(
        "--language",
        choices=LANGUAGES,
        default="python",
        help="Programming language (default: python)",
    )
    parser.add_argument(
        "--path", default=".", help="Output directory (default: current directory)"
    )

    args = parser.parse_args()

    project_path = Path(args.path) / args.name
    project_path.mkdir(parents=True, exist_ok=True)

    if args.language == "python":
        create_python_project(project_path, args.platform)
    else:
        create_typescript_project(project_path, args.platform)

    print(f"Created {args.language} chatbot project at: {project_path}")
    print(f"Platform: {args.platform}")
    print()
    print("Next steps:")
    if args.language == "python":
        print(f"  cd {project_path}")
        print("  pip install -r requirements.txt")
        print("  # Set environment variables for your platform")
        print("  python -m src.main")
    else:
        print(f"  cd {project_path}")
        print("  npm install")
        print("  # Set environment variables for your platform")
        print("  npm run dev")


if __name__ == "__main__":
    main()
