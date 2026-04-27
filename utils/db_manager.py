import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="eye_trainer",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        self.conn.autocommit = False

    def execute(self, query, params=None, fetch=False):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[DB] Ошибка: {e}")
            raise

    def insert_and_get_id(self, query, params=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query + " RETURNING id", params)
                new_id = cur.fetchone()[0]
                self.conn.commit()
                return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"[DB] Ошибка: {e}")
            raise

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
