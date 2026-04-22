from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core.bot_content_manager import BotContentManager
from services.transaction_validator import TransactionValidator
from states.user_onboarding_states import UserOnboardingStates, UserTransactionStates
from keyboards.transaction_category_keyboard_builder import TransactionCategoryKeyboardBuilder

from database.database_session_manager import DatabaseSessionManager
from repositories.user_repository import UserRepository
from repositories.transaction_repository import TransactionRepository
from services.user_service import UserService
from services.transaction_service import TransactionService
from services.monthly_stats_service import MonthlyStatsService
from aiogram.types import Message, CallbackQuery, FSInputFile
from services.export_service import ExportService

user_router = Router()


def format_amount_for_user(amount: Decimal) -> str:
    return f"{amount} ₽"

async def send_main_vault_screen(
    target_message: Message,
    telegram_user_id: int,
    content_manager: BotContentManager
):
    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        transaction_service = TransactionService(transaction_repository=transaction_repository)

        user_balance = transaction_service.get_user_balance(telegram_id=telegram_user_id)

        main_vault_text = content_manager.get_screen_text(
            screen_name="main_vault",
            achievement="",
            balance=format_amount_for_user(user_balance),
            quote="Кря! Главное держать хранилище под контролем."
        )

        await target_message.answer(text=main_vault_text)

    finally:
        session.close()

@user_router.message(Command("help"))
async def process_help_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    await state.clear()

    help_text = content_manager.get_screen_text(screen_name="help_rules")
    await message.answer(text=help_text)

@user_router.message(Command("balance"))
async def process_balance_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    await state.clear()

    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)

        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )
        monthly_stats_service = MonthlyStatsService(
            transaction_repository=transaction_repository
        )

        telegram_user_id = message.from_user.id

        current_balance = transaction_service.get_user_balance(
            telegram_id=telegram_user_id
        )

        monthly_stats = monthly_stats_service.get_current_month_stats(
            telegram_id=telegram_user_id
        )

        monthly_balance_text = content_manager.get_screen_text(
            screen_name="monthly_balance",
            income_for_month=format_amount_for_user(monthly_stats["income_for_month"]),
            expense_for_month=format_amount_for_user(monthly_stats["expense_for_month"]),
            current_balance=format_amount_for_user(current_balance),
        )

        await message.answer(text=monthly_balance_text)

    finally:
        session.close()

@user_router.message(Command("export"))
async def process_export_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    await state.clear()

    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        export_service = ExportService(transaction_repository=transaction_repository)

        telegram_user_id = message.from_user.id

        csv_file_path = export_service.generate_user_csv_export(
            telegram_id=telegram_user_id
        )

        export_ready_text = content_manager.get_screen_text(screen_name="export_ready")

        await message.answer(text=export_ready_text)

        csv_file = FSInputFile(csv_file_path)
        await message.answer_document(document=csv_file)

    finally:
        session.close()

@user_router.message(Command("vault"))
async def process_vault_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):

    await state.clear()

    await send_main_vault_screen(
        target_message=message,
        telegram_user_id=message.from_user.id,
        content_manager=content_manager
    )


def get_category_name_from_callback(callback_data: str) -> str:
    category_map = {
        "income_salary": "Зарплата",
        "income_business_freelance": "Бизнес",
        "income_gifts": "Подарки",
        "income_interest": "Проценты",
        "income_refund": "Возврат",
        "expense_products": "Продукты",
        "expense_cafe": "Кафе",
        "expense_housing": "Жилье",
        "expense_transport": "Транспорт",
        "expense_health": "Здоровье",
        "expense_clothes": "Одежда",
        "expense_subscriptions": "Подписки",
        "expense_entertainment": "Развлечения",
        "expense_hobby": "Хобби",
        "expense_debts": "Долги",
        "expense_other": "Прочее",
    }
    return category_map.get(callback_data, "Неизвестная категория")


def get_easter_egg_key(callback_data: str, amount: Decimal) -> str | None:
    if callback_data == "expense_hobby":
        return "hobby_education"

    if callback_data == "expense_clothes":
        return "clothes"

    if callback_data == "income_business_freelance" and amount > 0:
        return "business"

    return None


@user_router.message(CommandStart())
async def process_start_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
    await state.clear()

    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )

        telegram_user_id = message.from_user.id

        user_has_initial_capital = transaction_service.user_has_initial_capital(
            telegram_id=telegram_user_id
        )

        if user_has_initial_capital:
            await send_main_vault_screen(
                target_message=message,
                telegram_user_id=telegram_user_id,
                content_manager=content_manager
            )
            return

        await state.set_state(UserOnboardingStates.waiting_for_initial_capital)

        welcome_text = content_manager.get_screen_text(screen_name="start_onboarding")
        await message.answer(text=welcome_text)

    finally:
        session.close()


@user_router.message(Command("reset_me"))
async def process_reset_me_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager
):
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
    state: FSMContext,
    content_manager: BotContentManager
):
    is_valid, amount, error_key = TransactionValidator.validate_amount(message.text)

    if not is_valid:
        error_text = content_manager.get_screen_text(screen_name=error_key)
        await message.answer(text=error_text)
        return

    if amount > 0:
        screen_name = "income_category"
        transaction_type = "income"
    else:
        screen_name = "expense_category"
        transaction_type = "expense"

    await state.set_state(UserTransactionStates.waiting_for_category_selection)
    await state.update_data(
        pending_amount=str(amount),
        pending_transaction_type=transaction_type,
        user_message_id=message.message_id
    )

    keyboard_builder = TransactionCategoryKeyboardBuilder(content_manager)
    category_keyboard = keyboard_builder.build_keyboard_for_screen(screen_name=screen_name)

    category_text = content_manager.get_screen_text(
        screen_name=screen_name,
        amount=format_amount_for_user(amount)
    )

    await message.answer(
        text=category_text,
        reply_markup=category_keyboard
    )


@user_router.callback_query(
    UserTransactionStates.waiting_for_category_selection,
    F.data == "cancel_transaction"
)
async def process_cancel_transaction(
    callback: CallbackQuery,
    state: FSMContext,
    content_manager: BotContentManager
):
    state_data = await state.get_data()
    user_message_id = state_data.get("user_message_id")

    # Сначала очищаем состояние
    await state.clear()

    # Удаление сообщение бота с inline-кнопками
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Попытка удалить сообщение пользователя
    if user_message_id is not None:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=user_message_id
            )
        except Exception:
            pass

    await callback.answer("Операция отменена")


@user_router.callback_query(
    UserTransactionStates.waiting_for_category_selection,
    F.data.startswith("income_") | F.data.startswith("expense_")
)
async def process_category_selection(
    callback: CallbackQuery,
    state: FSMContext,
    content_manager: BotContentManager
):
    state_data = await state.get_data()

    pending_amount_text = state_data.get("pending_amount")
    pending_transaction_type = state_data.get("pending_transaction_type")

    if pending_amount_text is None or pending_transaction_type is None:
        await state.clear()
        await callback.answer("Состояние операции потеряно. Попробуй ввести сумму заново.")
        return

    amount = Decimal(pending_amount_text)
    callback_data = callback.data
    category_name = get_category_name_from_callback(callback_data)

    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        transaction_service = TransactionService(transaction_repository=transaction_repository)

        telegram_user = callback.from_user

        transaction_service.add_transaction(
            telegram_id=telegram_user.id,
            amount=amount,
            category=category_name,
            transaction_type=pending_transaction_type
        )

        easter_egg_text = ""
        easter_egg_key = get_easter_egg_key(callback_data=callback_data, amount=amount)

        if easter_egg_key is not None:
            easter_egg_text = content_manager.get_easter_egg_text(easter_egg_key)

        success_text = content_manager.get_screen_text(
            screen_name="success",
            amount=format_amount_for_user(amount),
            category=category_name,
            easter_egg=easter_egg_text
        )

        await callback.message.edit_text(text=success_text)
        await callback.answer()
        await state.clear()

    finally:
        session.close()