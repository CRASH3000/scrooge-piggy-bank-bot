import asyncio
import os
import logging

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from core.bot_content_manager import BotContentManager
from handlers.user_handlers import user_router

load_dotenv()


class ScroogeBotApplication:

    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")

        self.bot = Bot(token=self.bot_token)
        self.dispatcher = Dispatcher(storage=MemoryStorage())

        self.content_manager = BotContentManager(filepath="core/lexicon.yaml")
        self.dispatcher["content_manager"] = self.content_manager

        self.dispatcher.include_router(user_router)

    async def setup_bot_commands(self):

        bot_commands = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="vault", description="Мое хранилище"),
            BotCommand(command="balance", description="Отчет за месяц"),
            BotCommand(command="export", description="Выгрузить Гроссбух"),
            BotCommand(command="help", description="Правила"),
            BotCommand(command="reset_me", description="Сбросить мои данные"),
        ]

        await self.bot.set_my_commands(bot_commands)

    async def start_listening_for_messages(self):
        await self.setup_bot_commands()

        logging.info("Бот 'Копилка Скруджа' запущен и готов к работе!")
        await self.dispatcher.start_polling(self.bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot_app = ScroogeBotApplication()
    asyncio.run(bot_app.start_listening_for_messages())