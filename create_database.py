from database.database_initializer import create_all_database_tables


if __name__ == "__main__":
    create_all_database_tables()
    print("База данных и таблицы успешно созданы.")