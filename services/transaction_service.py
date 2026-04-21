from decimal import Decimal

from repositories.transaction_repository import TransactionRepository


class TransactionService:

    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def add_transaction(
        self,
        telegram_id: int,
        amount: Decimal,
        category: str,
        transaction_type: str
    ):

        return self.transaction_repository.create_transaction(
            telegram_id=telegram_id,
            amount=amount,
            category=category,
            transaction_type=transaction_type
        )

    def get_user_balance(self, telegram_id: int) -> Decimal:

        all_transactions = self.transaction_repository.get_all_user_transactions(telegram_id)

        total_balance = Decimal("0.00")

        for transaction in all_transactions:
            total_balance += Decimal(transaction.amount)

        return total_balance