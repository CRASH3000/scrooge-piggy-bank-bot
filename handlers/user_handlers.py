import os
from datetime import datetime
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    BotCommand,
    BotCommandScopeChat,
)

from core.bot_content_manager import BotContentManager
from database.database_session_manager import DatabaseSessionManager
from keyboards.transaction_category_keyboard_builder import (
    TransactionCategoryKeyboardBuilder,
)
from repositories.transaction_repository import TransactionRepository
from repositories.user_repository import UserRepository
from services.export_service import ExportService
from services.monthly_spending_category_achievement_service import (
    MonthlySpendingCategoryAchievementService,
)
from services.monthly_stats_service import MonthlyStatsService
from services.transaction_reaction_service import TransactionReactionService
from services.transaction_service import TransactionService
from services.transaction_validator import TransactionValidator
from services.user_service import UserService
from services.vault_balance_level_and_rank_service import (
    VaultBalanceLevelAndRankService,
)
from states.user_onboarding_states import (
    UserOnboardingStates,
    UserTransactionStates,
)

user_router = Router()


def format_amount_for_user(amount: Decimal) -> str:
    return f"{amount} ₽"


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
        "expense_education": "Учеба",
        "expense_debts": "Долги",
        "expense_other": "Прочее",
    }
    return category_map.get(callback_data, "Неизвестная категория")


def get_easter_egg_key(callback_data: str, amount: Decimal) -> str | None:
    absolute_amount = abs(amount)

    if callback_data == "expense_education" and absolute_amount >= Decimal("500"):
        return "education"

    if callback_data == "expense_clothes" and absolute_amount >= Decimal("3000"):
        return "clothes"

    if callback_data == "income_business_freelance" and amount >= Decimal("5000"):
        return "business"

    if callback_data == "expense_cafe" and absolute_amount >= Decimal("1500"):
        return "cafe"

    if callback_data == "expense_entertainment" and absolute_amount >= Decimal("2500"):
        return "entertainment"

    if callback_data == "expense_subscriptions" and absolute_amount >= Decimal("500"):
        return "subscriptions"

    if callback_data == "expense_debts" and absolute_amount >= Decimal("1000"):
        return "debts"

    if callback_data == "income_interest" and amount > 0:
        return "interest"

    if callback_data == "income_gifts" and amount >= Decimal("1000"):
        return "gifts"

    return None


def build_local_photo_input_file_if_path_exists(
    local_image_path: str,
) -> FSInputFile | None:
    if local_image_path and os.path.exists(local_image_path):
        return FSInputFile(local_image_path)

    return None


async def setup_commands_for_new_user_in_current_chat(message: Message):
    new_user_bot_commands = [
        BotCommand(command="start", description="Начать работу"),
    ]

    await message.bot.set_my_commands(
        commands=new_user_bot_commands,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )


async def setup_commands_for_registered_user_in_current_chat(message: Message):
    registered_user_bot_commands = [
        BotCommand(command="vault", description="Мое хранилище"),
        BotCommand(command="balance", description="Отчет за месяц"),
        BotCommand(command="export", description="Выгрузить Гроссбух"),
        BotCommand(command="help", description="Правила"),
        BotCommand(command="reset_me", description="Сбросить мои данные"),
    ]

    await message.bot.set_my_commands(
        commands=registered_user_bot_commands,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )


async def send_start_onboarding_screen(
    target_message: Message,
    content_manager: BotContentManager,
):
    onboarding_text = content_manager.get_screen_text(
        screen_name="start_onboarding"
    )
    onboarding_image_path = content_manager.get_screen_image_path(
        screen_name="start_onboarding"
    )
    onboarding_photo = build_local_photo_input_file_if_path_exists(
        local_image_path=onboarding_image_path
    )

    if onboarding_photo is not None:
        await target_message.answer_photo(
            photo=onboarding_photo,
            caption=onboarding_text,
        )
    else:
        await target_message.answer(text=onboarding_text)


async def send_main_vault_screen(
    target_message: Message,
    telegram_user_id: int,
    content_manager: BotContentManager,
    use_default_first_quote: bool = False,
):
    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )

        user_balance = transaction_service.get_user_balance(
            telegram_id=telegram_user_id
        )

        vault_level_rank_and_image_data = (
            VaultBalanceLevelAndRankService.get_vault_level_rank_and_image_key_by_balance(
                balance=user_balance
            )
        )

        if use_default_first_quote:
            vault_screen_quote = (
                content_manager.get_default_first_vault_screen_quote()
            )
        else:
            vault_screen_quote = (
                content_manager.get_random_financial_literacy_quote_for_vault_screen()
            )

        main_vault_text = content_manager.get_screen_text(
            screen_name="main_vault",
            balance=format_amount_for_user(user_balance),
            vault_level_number=vault_level_rank_and_image_data["vault_level_number"],
            vault_rank_name=vault_level_rank_and_image_data["vault_rank_name"],
            quote=vault_screen_quote,
        )

        vault_screen_image_path = (
            content_manager.get_vault_screen_image_path_by_image_key(
                vault_image_key=vault_level_rank_and_image_data["vault_image_key"]
            )
        )
        vault_screen_photo = build_local_photo_input_file_if_path_exists(
            local_image_path=vault_screen_image_path
        )

        if vault_screen_photo is not None:
            await target_message.answer_photo(
                photo=vault_screen_photo,
                caption=main_vault_text,
            )
        else:
            await target_message.answer(text=main_vault_text)

    finally:
        session.close()


async def send_monthly_balance_screen(
    target_message: Message,
    telegram_user_id: int,
    content_manager: BotContentManager,
):
    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)

        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )
        monthly_stats_service = MonthlyStatsService(
            transaction_repository=transaction_repository
        )
        monthly_spending_category_achievement_service = (
            MonthlySpendingCategoryAchievementService(
                transaction_repository=transaction_repository
            )
        )

        current_balance = transaction_service.get_user_balance(
            telegram_id=telegram_user_id
        )

        monthly_stats = monthly_stats_service.get_current_month_stats(
            telegram_id=telegram_user_id
        )

        current_datetime = datetime.now()

        monthly_achievement_text = (
            monthly_spending_category_achievement_service.get_monthly_achievement_text(
                telegram_id=telegram_user_id,
                year=current_datetime.year,
                month=current_datetime.month,
            )
        )

        monthly_balance_text = content_manager.get_screen_text(
            screen_name="monthly_balance",
            achievement=monthly_achievement_text,
            income_for_month=format_amount_for_user(
                monthly_stats["income_for_month"]
            ),
            expense_for_month=format_amount_for_user(
                monthly_stats["expense_for_month"]
            ),
            current_balance=format_amount_for_user(current_balance),
        )

        monthly_balance_image_path = content_manager.get_screen_image_path(
            screen_name="monthly_balance"
        )
        monthly_balance_photo = build_local_photo_input_file_if_path_exists(
            local_image_path=monthly_balance_image_path
        )

        if monthly_balance_photo is not None:
            await target_message.answer_photo(
                photo=monthly_balance_photo,
                caption=monthly_balance_text,
            )
        else:
            await target_message.answer(text=monthly_balance_text)

    finally:
        session.close()


async def start_new_transaction_category_selection(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
    amount: Decimal,
):
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
        user_message_id=message.message_id,
    )

    keyboard_builder = TransactionCategoryKeyboardBuilder(content_manager)
    category_keyboard = keyboard_builder.build_keyboard_for_screen(
        screen_name=screen_name
    )

    category_text = content_manager.get_screen_text(
        screen_name=screen_name,
        amount=format_amount_for_user(amount),
    )

    bot_category_message = await message.answer(
        text=category_text,
        reply_markup=category_keyboard,
    )

    await state.update_data(
        active_category_selection_bot_message_id=bot_category_message.message_id
    )


async def delete_previous_transaction_selection_messages_if_they_exist(
    message: Message,
    state: FSMContext,
):
    current_state_data = await state.get_data()

    previous_active_category_selection_bot_message_id = current_state_data.get(
        "active_category_selection_bot_message_id"
    )
    previous_user_message_id = current_state_data.get("user_message_id")

    if previous_active_category_selection_bot_message_id is not None:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=previous_active_category_selection_bot_message_id,
            )
        except Exception:
            pass

    if previous_user_message_id is not None:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=previous_user_message_id,
            )
        except Exception:
            pass


async def ensure_user_completed_onboarding_before_registered_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
) -> bool:
    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )

        user_has_initial_capital = transaction_service.user_has_initial_capital(
            telegram_id=message.from_user.id
        )

        if user_has_initial_capital:
            return True

        await setup_commands_for_new_user_in_current_chat(message)
        await state.set_state(UserOnboardingStates.waiting_for_initial_capital)

        await send_start_onboarding_screen(
            target_message=message,
            content_manager=content_manager,
        )

        return False

    finally:
        session.close()


@user_router.message(CommandStart())
async def process_start_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
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
            await setup_commands_for_registered_user_in_current_chat(message)

            await send_main_vault_screen(
                target_message=message,
                telegram_user_id=telegram_user_id,
                content_manager=content_manager,
            )
            return

        await setup_commands_for_new_user_in_current_chat(message)

        await state.set_state(UserOnboardingStates.waiting_for_initial_capital)

        await send_start_onboarding_screen(
            target_message=message,
            content_manager=content_manager,
        )

    finally:
        session.close()


@user_router.message(Command("vault"))
async def process_vault_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    await state.clear()

    user_completed_onboarding = (
        await ensure_user_completed_onboarding_before_registered_command(
            message=message,
            state=state,
            content_manager=content_manager,
        )
    )

    if not user_completed_onboarding:
        return

    await setup_commands_for_registered_user_in_current_chat(message)

    await send_main_vault_screen(
        target_message=message,
        telegram_user_id=message.from_user.id,
        content_manager=content_manager,
    )


@user_router.message(Command("balance"))
async def process_balance_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    await state.clear()

    user_completed_onboarding = (
        await ensure_user_completed_onboarding_before_registered_command(
            message=message,
            state=state,
            content_manager=content_manager,
        )
    )

    if not user_completed_onboarding:
        return

    await setup_commands_for_registered_user_in_current_chat(message)

    await send_monthly_balance_screen(
        target_message=message,
        telegram_user_id=message.from_user.id,
        content_manager=content_manager,
    )


@user_router.message(Command("export"))
async def process_export_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    await state.clear()

    user_completed_onboarding = (
        await ensure_user_completed_onboarding_before_registered_command(
            message=message,
            state=state,
            content_manager=content_manager,
        )
    )

    if not user_completed_onboarding:
        return

    await setup_commands_for_registered_user_in_current_chat(message)

    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        export_service = ExportService(transaction_repository=transaction_repository)

        telegram_user_id = message.from_user.id

        csv_file_path = export_service.generate_user_csv_export(
            telegram_id=telegram_user_id
        )

        export_ready_text = content_manager.get_screen_text(
            screen_name="export_ready"
        )

        await message.answer(text=export_ready_text)

        csv_file = FSInputFile(csv_file_path)
        await message.answer_document(document=csv_file)

    finally:
        session.close()


@user_router.message(Command("help"))
async def process_help_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    await state.clear()

    user_completed_onboarding = (
        await ensure_user_completed_onboarding_before_registered_command(
            message=message,
            state=state,
            content_manager=content_manager,
        )
    )

    if not user_completed_onboarding:
        return

    await setup_commands_for_registered_user_in_current_chat(message)

    help_text = content_manager.get_screen_text(screen_name="help_rules")
    await message.answer(text=help_text)


@user_router.message(Command("reset_me"))
async def process_reset_me_command(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    await state.clear()

    user_completed_onboarding = (
        await ensure_user_completed_onboarding_before_registered_command(
            message=message,
            state=state,
            content_manager=content_manager,
        )
    )

    if not user_completed_onboarding:
        return

    session = DatabaseSessionManager.create_session()

    try:
        user_repository = UserRepository(session=session)
        user_service = UserService(user_repository=user_repository)

        telegram_user = message.from_user

        was_deleted = user_service.delete_user_with_all_data(
            telegram_id=telegram_user.id
        )

        if was_deleted:
            await setup_commands_for_new_user_in_current_chat(message)

            success_text = content_manager.get_screen_text(
                screen_name="reset_success"
            )
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
    content_manager: BotContentManager,
):
    is_valid, amount, error_key = TransactionValidator.validate_initial_capital(
        message.text
    )

    if not is_valid:
        error_text = content_manager.get_screen_text(screen_name=error_key)
        await message.answer(text=error_text)
        return

    if amount is None:
        error_text = content_manager.get_screen_text(
            screen_name="validation_error"
        )
        await message.answer(text=error_text)
        return

    session = DatabaseSessionManager.create_session()

    try:
        user_repository = UserRepository(session=session)
        transaction_repository = TransactionRepository(session=session)

        user_service = UserService(user_repository=user_repository)
        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )

        telegram_user = message.from_user

        user_service.create_or_update_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
        )

        transaction_service.add_transaction(
            telegram_id=telegram_user.id,
            amount=amount,
            category="initial_capital",
            transaction_type="income",
        )

        await setup_commands_for_registered_user_in_current_chat(message)

        await state.clear()

        await send_main_vault_screen(
            target_message=message,
            telegram_user_id=telegram_user.id,
            content_manager=content_manager,
            use_default_first_quote=True,
        )

    finally:
        session.close()


@user_router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def process_transaction_input(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    is_valid, amount, error_key = TransactionValidator.validate_amount(
        message.text
    )

    if not is_valid:
        error_text = content_manager.get_screen_text(screen_name=error_key)
        await message.answer(text=error_text)
        return

    await start_new_transaction_category_selection(
        message=message,
        state=state,
        content_manager=content_manager,
        amount=amount,
    )


@user_router.message(
    UserTransactionStates.waiting_for_category_selection,
    F.text & ~F.text.startswith("/")
)
async def process_transaction_input_while_category_selection_is_active(
    message: Message,
    state: FSMContext,
    content_manager: BotContentManager,
):
    await delete_previous_transaction_selection_messages_if_they_exist(
        message=message,
        state=state,
    )

    is_valid, amount, error_key = TransactionValidator.validate_amount(
        message.text
    )

    if not is_valid:
        error_text = content_manager.get_screen_text(screen_name=error_key)
        await message.answer(text=error_text)
        return

    await start_new_transaction_category_selection(
        message=message,
        state=state,
        content_manager=content_manager,
        amount=amount,
    )


@user_router.callback_query(
    UserTransactionStates.waiting_for_category_selection,
    F.data == "cancel_transaction"
)
async def process_cancel_transaction(
    callback: CallbackQuery,
    state: FSMContext,
):
    state_data = await state.get_data()
    user_message_id = state_data.get("user_message_id")

    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        pass

    if user_message_id is not None:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=user_message_id,
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
    content_manager: BotContentManager,
):
    state_data = await state.get_data()

    pending_amount_text = state_data.get("pending_amount")
    pending_transaction_type = state_data.get("pending_transaction_type")

    if pending_amount_text is None or pending_transaction_type is None:
        await state.clear()
        await callback.answer(
            "Состояние операции потеряно. Попробуй ввести сумму заново."
        )
        return

    amount = Decimal(pending_amount_text)
    callback_data = callback.data
    category_name = get_category_name_from_callback(callback_data)

    session = DatabaseSessionManager.create_session()

    try:
        transaction_repository = TransactionRepository(session=session)
        transaction_service = TransactionService(
            transaction_repository=transaction_repository
        )
        transaction_reaction_service = TransactionReactionService(
            transaction_repository=transaction_repository
        )

        telegram_user = callback.from_user

        transaction_service.add_transaction(
            telegram_id=telegram_user.id,
            amount=amount,
            category=category_name,
            transaction_type=pending_transaction_type,
        )

        easter_egg_text = ""

        easter_egg_key = get_easter_egg_key(
            callback_data=callback_data,
            amount=amount,
        )

        if easter_egg_key is None:
            easter_egg_key = (
                transaction_reaction_service.get_smart_reaction_key_for_current_transaction(
                    telegram_id=telegram_user.id,
                    current_transaction_category_name=category_name,
                    current_transaction_type=pending_transaction_type,
                )
            )

        if easter_egg_key is not None:
            easter_egg_text = content_manager.get_easter_egg_text(
                easter_egg_key
            )

        success_text = content_manager.get_screen_text(
            screen_name="success",
            amount=format_amount_for_user(amount),
            category=category_name,
            easter_egg=easter_egg_text,
        )

        await callback.message.edit_text(text=success_text)
        await callback.answer()
        await state.clear()

    finally:
        session.close()