from utils.db_manager import DatabaseManager
from repositories.user_repository import UserRepository

db = DatabaseManager()
repo = UserRepository(db)

user_id = repo.create_user("Алексей", 28)
print("Создан пользователь:", user_id)

users = repo.get_all()
print("Все пользователи:", users)
