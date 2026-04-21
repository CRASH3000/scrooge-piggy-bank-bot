import re
from decimal import Decimal, InvalidOperation


class TransactionValidator:
    """
    Сервис для проверки введенных пользователем сумм (FR-2).
    Изолирован от Telegram API, работает только с чистыми данными.
    """

    @staticmethod
    def validate_amount(text: str) -> tuple[bool, Decimal | None, str | None]:
        """
        Общая проверка суммы по правилам ТЗ.
        Возвращает:
        (успешно_или_нет, сумма_decimal, ключ_ошибки)
        """
        cleaned_text = text.strip()

        if not re.fullmatch(r"^[+-]?\d+(\.\d{1,2})?$", cleaned_text):
            return False, None, "validation_error"

        try:
            amount = Decimal(cleaned_text)
        except InvalidOperation:
            return False, None, "validation_error"

        if amount == 0:
            return False, None, "validation_error"

        if amount > Decimal("999999999"):
            return False, None, "limit_error_income"

        if amount < Decimal("-999999999"):
            return False, None, "limit_error_expense"

        return True, amount, None

    @staticmethod
    def validate_initial_capital(text: str) -> tuple[bool, Decimal | None, str | None]:
        is_valid, amount, error_key = TransactionValidator.validate_amount(text)

        if not is_valid:
            return False, None, error_key

        if amount is None:
            return False, None, "validation_error"

        if amount <= 0:
            return False, None, "validation_error"

        return True, amount, None