from sqlalchemy.orm import Session

from database.database_models import User


class UserRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_user_by_telegram_id(self, telegram_id: int) -> User | None:

        return (
            self.session.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )

    def create_user(self, telegram_id: int, username: str | None) -> User:

        new_user = User(
            telegram_id=telegram_id,
            username=username
        )
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user

    def delete_user_by_telegram_id(self, telegram_id: int) -> bool:

        user = self.get_user_by_telegram_id(telegram_id)

        if user is None:
            return False

        self.session.delete(user)
        self.session.commit()
        return True