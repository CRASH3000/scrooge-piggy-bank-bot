from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.bot_content_manager import BotContentManager


class TransactionCategoryKeyboardBuilder:
    def __init__(self, content_manager: BotContentManager):
        self.content_manager = content_manager

    def build_keyboard_for_screen(self, screen_name: str) -> InlineKeyboardMarkup:
        keyboard_builder = InlineKeyboardBuilder()

        buttons = self.content_manager.get_screen_buttons(screen_name)

        for button_data in buttons:
            keyboard_builder.add(
                InlineKeyboardButton(
                    text=button_data["text"],
                    callback_data=button_data["callback_data"]
                )
            )

        cancel_button = self.content_manager.get_cancel_button(screen_name)
        if cancel_button:
            keyboard_builder.add(
                InlineKeyboardButton(
                    text=cancel_button["text"],
                    callback_data=cancel_button["callback_data"]
                )
            )

        if screen_name == "income_category":
            keyboard_builder.adjust(2, 2, 1, 1)
        elif screen_name == "expense_category":
            keyboard_builder.adjust(2, 2, 2, 2, 2, 1)
        else:
            keyboard_builder.adjust(1)

        return keyboard_builder.as_markup()