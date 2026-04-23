from datetime import datetime
from decimal import Decimal

from repositories.transaction_repository import TransactionRepository


class TransactionReactionService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def get_smart_reaction_key_for_current_transaction(
        self,
        telegram_id: int,
        current_transaction_category_name: str,
        current_transaction_type: str,
    ) -> str | None:
        current_datetime = datetime.now()

        user_transactions_for_current_month = (
            self.transaction_repository.get_user_transactions_for_month(
                telegram_id=telegram_id,
                year=current_datetime.year,
                month=current_datetime.month,
            )
        )

        if (
            current_transaction_type == "expense"
            and current_transaction_category_name == "Прочее"
        ):
            other_expense_operations_count_for_current_month = 0

            for transaction in user_transactions_for_current_month:
                if (
                    transaction.type == "expense"
                    and transaction.category == "Прочее"
                ):
                    other_expense_operations_count_for_current_month += 1

            if other_expense_operations_count_for_current_month >= 8:
                return "too_many_other_expenses"

        if (
            current_transaction_type == "expense"
            and current_transaction_category_name == "Развлечения"
        ):
            total_expense_amount_for_current_month = Decimal("0.00")
            entertainment_expense_amount_for_current_month = Decimal("0.00")

            for transaction in user_transactions_for_current_month:
                if transaction.type != "expense":
                    continue

                transaction_amount = abs(Decimal(transaction.amount))
                total_expense_amount_for_current_month += transaction_amount

                if transaction.category == "Развлечения":
                    entertainment_expense_amount_for_current_month += transaction_amount

            if total_expense_amount_for_current_month > Decimal("0.00"):
                entertainment_expense_share_percent = (
                    entertainment_expense_amount_for_current_month
                    / total_expense_amount_for_current_month
                ) * Decimal("100")

                if entertainment_expense_share_percent >= Decimal("30"):
                    return "too_much_entertainment_share"

        if (
            current_transaction_type == "expense"
            and current_transaction_category_name == "Кафе"
        ):
            cafe_expense_operations_count_for_current_month = 0

            for transaction in user_transactions_for_current_month:
                if (
                    transaction.type == "expense"
                    and transaction.category == "Кафе"
                ):
                    cafe_expense_operations_count_for_current_month += 1

            if cafe_expense_operations_count_for_current_month >= 5:
                return "too_many_cafe_expenses"

        return None