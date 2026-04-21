from repositories.user_repository import UserRepository


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_or_update_user(self, telegram_id: int, username: str | None):

        existing_user = self.user_repository.get_user_by_telegram_id(telegram_id)

        if existing_user is not None:
            return existing_user

        return self.user_repository.create_user(
            telegram_id=telegram_id,
            username=username
        )

    def delete_user_with_all_data(self, telegram_id: int) -> bool:

        return self.user_repository.delete_user_by_telegram_id(telegram_id)