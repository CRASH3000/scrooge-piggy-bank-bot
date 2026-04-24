import csv
import os
from datetime import datetime
from decimal import Decimal

from repositories.transaction_repository import TransactionRepository


class ExportService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def get_human_readable_category_name_for_csv(self, category_name: str) -> str:
        category_names_for_csv = {
            "initial_capital": "Стартовый капитал",
        }

        return category_names_for_csv.get(category_name, category_name)

    def generate_user_csv_export(self, telegram_id: int) -> str:
        all_transactions = (
            self.transaction_repository.get_all_user_transactions_ordered_by_timestamp(
                telegram_id=telegram_id
            )
        )

        os.makedirs("exports", exist_ok=True)

        export_created_at_for_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M")
        file_path = f"exports/Гроссбух_{export_created_at_for_file_name}.csv"

        total_balance = Decimal("0.00")
        initial_capital = Decimal("0.00")

        for transaction in all_transactions:
            transaction_amount = Decimal(transaction.amount)
            total_balance += transaction_amount

            if transaction.category == "initial_capital":
                initial_capital += transaction_amount

        with open(file_path, "w", encoding="utf-8-sig", newline="") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",")

            csv_writer.writerow([f"Стартовый капитал: {initial_capital:.2f} ₽"])
            csv_writer.writerow([])

            csv_writer.writerow(["Дата и время", "Сумма", "Категория"])

            for transaction in all_transactions:
                formatted_timestamp = transaction.timestamp.strftime("%d.%m.%Y %H:%M")
                formatted_amount = f"{Decimal(transaction.amount):.2f} ₽"

                human_readable_category_name = (
                    self.get_human_readable_category_name_for_csv(
                        category_name=transaction.category
                    )
                )

                csv_writer.writerow(
                    [
                        formatted_timestamp,
                        formatted_amount,
                        human_readable_category_name,
                    ]
                )

            csv_writer.writerow([])
            csv_writer.writerow([f"Итоговый баланс: {total_balance:.2f} ₽"])

        return file_path