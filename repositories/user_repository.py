from utils.db_manager import DatabaseManager


class UserRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_user(self, name: str, age: int) -> int:
        query = """
            INSERT INTO users (name, age)
            VALUES (%s, %s)
            RETURNING id;
        """
        result = self.db.execute(query, (name, age), fetch=True)
        return result[0][0]

    def get_by_id(self, user_id: int):
        result = self.db.execute(
            "SELECT * FROM users WHERE id = %s;", (user_id,), fetch=True
        )
        return result[0] if result else None

    def get_all(self):
        return self.db.execute("SELECT * FROM users;", fetch=True)

    def save_medical(self, user_id: int, disease: str, severity: int):
        self.db.execute(
            "INSERT INTO user_medical (user_id, disease, severity) VALUES (%s, %s, %s);",
            (user_id, disease, severity)
        )

    def save_preferences(self, user_id: int, theme: str, interests: list):
        self.db.execute(
            "INSERT INTO user_preferences (user_id, theme, interests) VALUES (%s, %s, %s);",
            (user_id, theme, interests)
        )
