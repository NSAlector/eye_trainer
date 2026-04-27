from utils.db_manager import DatabaseManager


class TestRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def start_session(self, user_id: int, test_id: int) -> int:
        result = self.db.execute(
            """
            INSERT INTO test_sessions (user_id, test_id)
            VALUES (%s, %s) RETURNING id;
            """,
            (user_id, test_id), fetch=True
        )
        return result[0][0]

    def finish_session(self, session_id: int):
        self.db.execute(
            "UPDATE test_sessions SET finished_at = NOW() WHERE id = %s;",
            (session_id,)
        )

    def save_answer(self, session_id: int, question_id: int,
                    answer_id: int, is_correct: bool):
        self.db.execute(
            """
            INSERT INTO user_answers (session_id, question_id, answer_id, is_correct)
            VALUES (%s, %s, %s, %s);
            """,
            (session_id, question_id, answer_id, is_correct)
        )

    def save_result(self, session_id: int, correct: int, total: int):
        self.db.execute(
            """
            INSERT INTO test_results (session_id, correct_count, total_count)
            VALUES (%s, %s, %s);
            """,
            (session_id, correct, total)
        )

    def get_result(self, session_id: int):
        result = self.db.execute(
            "SELECT * FROM test_results WHERE session_id = %s;",
            (session_id,), fetch=True
        )
        return result[0] if result else None

    def save_decision(self, session_id: int, decision: str):
        self.db.execute(
            "INSERT INTO decisions (session_id, decision) VALUES (%s, %s);",
            (session_id, decision)
        )

    def get_decisions(self, session_id: int):
        return self.db.execute(
            "SELECT decision FROM decisions WHERE session_id = %s;",
            (session_id,), fetch=True
        )
