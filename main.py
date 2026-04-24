import asyncio
import os
import logging

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.bot_content_manager import BotContentManager
from handlers.user_handlers import user_router

load_dotenv()


class ScroogeBotApplication:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")

        self.bot = Bot(
            token=self.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dispatcher = Dispatcher(storage=MemoryStorage())

        self.content_manager = BotContentManager(filepath="core/lexicon.yaml")
        self.dispatcher["content_manager"] = self.content_manager

        self.dispatcher.include_router(user_router)

    async def start_listening_for_messages(self):
        logging.info("Бот 'Копилка Скруджа' запущен и готов к работе!")
        await self.dispatcher.start_polling(self.bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot_app = ScroogeBotApplication()
    asyncio.run(bot_app.start_listening_for_messages())