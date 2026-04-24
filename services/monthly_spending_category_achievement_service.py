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

        total_income_amount_for_month = Decimal("0.00")
        total_expense_amount_for_month = Decimal("0.00")

        expense_amount_by_category = {
            "Учеба": Decimal("0.00"),
            "Здоровье": Decimal("0.00"),
            "Развлечения": Decimal("0.00"),
            "Кафе": Decimal("0.00"),
            "Одежда": Decimal("0.00"),
            "Подписки": Decimal("0.00"),
            "Прочее": Decimal("0.00"),
        }

        expense_operations_count_by_category = {
            "Прочее": 0,
            "Кафе": 0,
            "Подписки": 0,
        }

        for transaction in user_transactions_for_month:
            transaction_amount = Decimal(transaction.amount)

            if transaction.type == "income":
                total_income_amount_for_month += transaction_amount
                continue

            if transaction.type != "expense":
                continue

            expense_amount = abs(transaction_amount)
            total_expense_amount_for_month += expense_amount

            if transaction.category in expense_amount_by_category:
                expense_amount_by_category[transaction.category] += expense_amount

            if transaction.category in expense_operations_count_by_category:
                expense_operations_count_by_category[transaction.category] += 1

        if total_income_amount_for_month == Decimal("0.00") and total_expense_amount_for_month == Decimal("0.00"):
            return ""

        if total_expense_amount_for_month == Decimal("0.00"):
            return "🏆 Железная выдержка: В этом месяце ты вообще не трогал свое хранилище."

        entertainment_percent = self._calculate_percent(
            part=expense_amount_by_category["Развлечения"],
            total=total_expense_amount_for_month
        )

        cafe_percent = self._calculate_percent(
            part=expense_amount_by_category["Кафе"],
            total=total_expense_amount_for_month
        )

        clothes_percent = self._calculate_percent(
            part=expense_amount_by_category["Одежда"],
            total=total_expense_amount_for_month
        )

        subscriptions_percent = self._calculate_percent(
            part=expense_amount_by_category["Подписки"],
            total=total_expense_amount_for_month
        )

        other_percent = self._calculate_percent(
            part=expense_amount_by_category["Прочее"],
            total=total_expense_amount_for_month
        )

        education_percent = self._calculate_percent(
            part=expense_amount_by_category["Учеба"],
            total=total_expense_amount_for_month
        )

        health_percent = self._calculate_percent(
            part=expense_amount_by_category["Здоровье"],
            total=total_expense_amount_for_month
        )

        if entertainment_percent >= Decimal("45"):
            return "🔴 Транжира месяца: Развлечения съели слишком большой кусок твоего капитала."

        if cafe_percent >= Decimal("30") or expense_operations_count_by_category["Кафе"] >= 8:
            return "🟠 Кофейный магнат: Похоже, кафе в этом месяце видело тебя слишком часто."

        if clothes_percent >= Decimal("35"):
            return "🟠 Модник месяца: Гардероб расцвел, а вот хранилище слегка приуныло."

        if subscriptions_percent >= Decimal("20") or expense_operations_count_by_category["Подписки"] >= 5:
            return "🟠 Подписочный пленник: Слишком много регулярных мелких трат грызут твой бюджет."

        if other_percent >= Decimal("25") or expense_operations_count_by_category["Прочее"] >= 8:
            return "🟠 Мастер 'Прочего': Пора разобраться, куда именно утекают монеты."

        if total_income_amount_for_month > Decimal("0.00") and total_expense_amount_for_month <= (
            total_income_amount_for_month * Decimal("0.50")
        ):
            return "🟢 Хранитель капитала: В этом месяце ты отлично держишь расходы под контролем."

        if education_percent >= Decimal("20"):
            return "🟢 Умник месяца: Похоже, ты вкладываешься не в шум, а в собственную голову."

        if health_percent >= Decimal("15"):
            return "🟢 Бережешь главное: В этом месяце ты не забыл, что здоровье дороже монет."

        if total_income_amount_for_month > Decimal("0.00") and total_expense_amount_for_month < total_income_amount_for_month:
            return "🟢 В плюсе: В этом месяце ты живешь по средствам и не даешь хранилищу худеть."

        return ""

    def _calculate_percent(self, part: Decimal, total: Decimal) -> Decimal:
        if total == Decimal("0.00"):
            return Decimal("0.00")

        return (part / total) * Decimal("100")