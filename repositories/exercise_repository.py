from utils.db_manager import DatabaseManager


class ExerciseRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_plan(self, user_id: int, plan: dict) -> int:
        self.db.execute(
            "DELETE FROM exercise_plans WHERE user_id = %s;",
            (user_id,)
        )
        result = self.db.execute(
            """
            INSERT INTO exercise_plans
                (user_id, disease, level, background_file,
                 object_hex, object_scale, speed_ms, exercises, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            RETURNING id;
            """,
            (
                user_id,
                plan.get("disease"),
                plan.get("level"),
                plan.get("background"),
                plan.get("object_hex"),
                plan.get("object_scale"),
                plan.get("speed_ms"),
                __import__("json").dumps(plan.get("exercises", []), ensure_ascii=False),
                __import__("json").dumps(plan.get("notes", []), ensure_ascii=False),
            ),
            fetch=True
        )
        return result[0][0]

    def get_plan(self, user_id: int) -> dict | None:
        result = self.db.execute(
            "SELECT * FROM exercise_plans WHERE user_id = %s;",
            (user_id,), fetch=True
        )
        if not result:
            return None
        row = result[0]
        return {
            "disease": row[2],
            "level": row[3],
            "background": row[4],
            "object_hex": row[5],
            "object_scale": float(row[6]) if row[6] else 1.0,
            "speed_ms": row[7],
            "exercises": row[8] if row[8] else [],
            "notes": row[9] if row[9] else [],
        }

    def save_session(self, user_id: int, exercise_name: str, score: int, avg_error: float, is_success: bool, anomalies: list) -> int:
        result = self.db.execute(
            """
            INSERT INTO exercise_history
                (user_id, exercise_name, score, avg_error, is_success, anomalies)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id;
            """,
            (
                user_id, exercise_name, score,
                round(avg_error, 3), is_success,
                __import__("json").dumps(anomalies, ensure_ascii=False),
            ),
            fetch=True
        )
        return result[0][0]

    def get_history(self, user_id: int, limit: int = 20) -> list:
        return self.db.execute(
            """
            SELECT exercise_name, score, avg_error, is_success, created_at
            FROM exercise_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (user_id, limit), fetch=True
        ) or []

    def get_last_scores(self, user_id: int, exercise_name: str) -> list:
        return self.db.execute(
            """
            SELECT score, is_success, created_at
            FROM exercise_history
            WHERE user_id = %s AND exercise_name = %s
            ORDER BY created_at DESC LIMIT 5;
            """,
            (user_id, exercise_name), fetch=True
        ) or []
