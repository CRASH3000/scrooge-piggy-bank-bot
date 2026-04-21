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