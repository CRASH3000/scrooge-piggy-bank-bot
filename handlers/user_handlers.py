from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from core.bot_content_manager import BotContentManager
from services.transaction_validator import TransactionValidator
from states.user_onboarding_states import UserOnboardingStates

from database.database_session_manager import DatabaseSessionManager
from repositories.user_repository import UserRepository
from repositories.transaction_repository import TransactionRepository
from services.user_service import UserService
from services.transaction_service import TransactionService

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


@user_router.message(Command("reset_me"))
async def process_reset_me_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    """
    Полностью удаляет данные текущего пользователя.
    Нужна для тестирования и повторного прохождения онбординга.
    """
    session = DatabaseSessionManager.create_session()

    try:
        user_repository = UserRepository(session=session)
        user_service = UserService(user_repository=user_repository)

        telegram_user = message.from_user

        was_deleted = user_service.delete_user_with_all_data(
            telegram_id=telegram_user.id
        )

        await state.clear()

        if was_deleted:
            success_text = content_manager.get_screen_text(screen_name="reset_success")
            await message.answer(text=success_text)
        else:
            nothing_text = content_manager.get_screen_text(
                screen_name="reset_nothing_to_delete"
            )
            await message.answer(text=nothing_text)

    finally:
        session.close()


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

    session = DatabaseSessionManager.create_session()

    try:
        user_repository = UserRepository(session=session)
        transaction_repository = TransactionRepository(session=session)

        user_service = UserService(user_repository=user_repository)
        transaction_service = TransactionService(transaction_repository=transaction_repository)

        telegram_user = message.from_user

        user_service.create_or_update_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username
        )

        transaction_service.add_transaction(
            telegram_id=telegram_user.id,
            amount=amount,
            category="initial_capital",
            transaction_type="income"
        )

        user_balance = transaction_service.get_user_balance(telegram_id=telegram_user.id)

        await state.clear()

        main_vault_text = content_manager.get_screen_text(
            screen_name="main_vault",
            achievement="",
            balance=format_amount_for_user(user_balance),
            quote="Кря! Начало положено — теперь главное не растратить всё сразу."
        )

        await message.answer(text=main_vault_text)

    finally:
        session.close()


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