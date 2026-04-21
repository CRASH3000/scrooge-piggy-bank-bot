from database.database_config import SessionLocal


class DatabaseSessionManager:

    @staticmethod
    def create_session():
        return SessionLocal()