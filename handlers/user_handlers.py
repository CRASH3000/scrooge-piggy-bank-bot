from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from core.bot_content_manager import BotContentManager
from services.transaction_validator import TransactionValidator
from states.user_onboarding_states import UserOnboardingStates

user_router = Router()


def format_amount_for_user(amount: Decimal) -> str:
    return f"{amount} ₽"


@user_router.message(CommandStart())
async def process_start_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    await state.set_state(UserOnboardingStates.waiting_for_initial_capital)

    welcome_text = content_manager.get_screen_text(screen_name="start_onboarding")
    await message.answer(text=welcome_text)


@user_router.message(
    UserOnboardingStates.waiting_for_initial_capital,
    F.text & ~F.text.startswith("/")
)
async def process_initial_capital_input(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    is_valid, amount, error_key = TransactionValidator.validate_initial_capital(message.text)

    if not is_valid:
        error_text = content_manager.get_screen_text(screen_name=error_key)
        await message.answer(text=error_text)
        return

    if amount is None:
        error_text = content_manager.get_screen_text(screen_name="validation_error")
        await message.answer(text=error_text)
        return

    await state.clear()

    main_vault_text = content_manager.get_screen_text(
        screen_name="main_vault",
        achievement="",
        balance=format_amount_for_user(amount),
        quote="Кря! Начало положено — теперь главное не растратить всё сразу."
    )

    await message.answer(text=main_vault_text)


@user_router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def process_transaction_input(
    message: Message,
    content_manager: BotContentManager
):
    is_valid, amount, error_key = TransactionValidator.validate_amount(message.text)

    if not is_valid:
        error_text = content_manager.get_screen_text(screen_name=error_key)
        await message.answer(text=error_text)
        return

    await message.answer(
        text=f"Отлично! Строгая проверка пройдена. Распознана сумма: {amount}"
    )