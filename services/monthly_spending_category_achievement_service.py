from decimal import Decimal

from repositories.transaction_repository import TransactionRepository


class MonthlySpendingCategoryAchievementService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def get_monthly_achievement_text(self, telegram_id: int, year: int, month: int) -> str:
        user_transactions_for_month = self.transaction_repository.get_user_transactions_for_month(
            telegram_id=telegram_id,
            year=year,
            month=month
        )

        total_expense_amount_for_month = Decimal("0.00")
        total_hobby_expense_amount_for_month = Decimal("0.00")
        total_entertainment_expense_amount_for_month = Decimal("0.00")

        for transaction in user_transactions_for_month:
            if transaction.type != "expense":
                continue

            transaction_amount = abs(Decimal(transaction.amount))
            total_expense_amount_for_month += transaction_amount

            if transaction.category == "Хобби":
                total_hobby_expense_amount_for_month += transaction_amount

            if transaction.category == "Развлечения":
                total_entertainment_expense_amount_for_month += transaction_amount

        if total_expense_amount_for_month == Decimal("0.00"):
            return ""

        hobby_percent = (
            total_hobby_expense_amount_for_month / total_expense_amount_for_month
        ) * Decimal("100")

        entertainment_percent = (
            total_entertainment_expense_amount_for_month / total_expense_amount_for_month
        ) * Decimal("100")

        if hobby_percent > Decimal("30"):
            return "🟢 Умник месяца: Инвестиции в знания растут!"

        if entertainment_percent > Decimal("50"):
            return "🔴 Транжира: Вечеринки съедают твой капитал!"

        return ""