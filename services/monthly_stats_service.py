from datetime import datetime
from decimal import Decimal

from repositories.transaction_repository import TransactionRepository


class MonthlyStatsService:

    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def get_current_month_stats(self, telegram_id: int) -> dict:

        now = datetime.now()

        monthly_transactions = self.transaction_repository.get_user_transactions_for_month(
            telegram_id=telegram_id,
            year=now.year,
            month=now.month
        )

        total_income_for_month = Decimal("0.00")
        total_expense_for_month = Decimal("0.00")

        for transaction in monthly_transactions:
            transaction_amount = Decimal(transaction.amount)

            if transaction.type == "income":
                total_income_for_month += transaction_amount

            if transaction.type == "expense":
                total_expense_for_month += abs(transaction_amount)

        return {
            "income_for_month": total_income_for_month,
            "expense_for_month": total_expense_for_month,
        }