from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from database.database_models import Transaction


class TransactionRepository:

    def __init__(self, session: Session):
        self.session = session

    def create_transaction(
        self,
        telegram_id: int,
        amount: Decimal,
        category: str,
        transaction_type: str
    ) -> Transaction:
        new_transaction = Transaction(
            telegram_id=telegram_id,
            amount=amount,
            category=category,
            type=transaction_type
        )
        self.session.add(new_transaction)
        self.session.commit()
        self.session.refresh(new_transaction)
        return new_transaction

    def get_all_user_transactions(self, telegram_id: int) -> list[Transaction]:
        return (
            self.session.query(Transaction)
            .filter(Transaction.telegram_id == telegram_id)
            .all()
        )

    def get_all_user_transactions_ordered_by_timestamp(
        self,
        telegram_id: int
    ) -> list[Transaction]:
        return (
            self.session.query(Transaction)
            .filter(Transaction.telegram_id == telegram_id)
            .order_by(Transaction.timestamp.asc())
            .all()
        )

    def get_user_transactions_for_month(
        self,
        telegram_id: int,
        year: int,
        month: int
    ) -> list[Transaction]:
        all_user_transactions = self.get_all_user_transactions(telegram_id=telegram_id)

        filtered_transactions = []

        for transaction in all_user_transactions:
            if transaction.timestamp.year == year and transaction.timestamp.month == month:
                filtered_transactions.append(transaction)

        return filtered_transactions

    def user_has_initial_capital_transaction(self, telegram_id: int) -> bool:
        initial_capital_transaction = (
            self.session.query(Transaction)
            .filter(
                Transaction.telegram_id == telegram_id,
                Transaction.category == "initial_capital"
            )
            .first()
        )

        return initial_capital_transaction is not None