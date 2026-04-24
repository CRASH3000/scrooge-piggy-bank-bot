from database.database_base import Base
from database.database_config import engine
from database import database_models


def create_all_database_tables():
    Base.metadata.create_all(bind=engine)