import sqlite3
from contextlib import contextmanager


@contextmanager
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    try:
        yield conn
    finally:
        conn.close()


class RepoClient:
    def __init__(self, db_name):
        self.db_name = db_name

    def create_chat_ai(self, custom_ai):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_ai (custom_ai) VALUES (?)
                """,
                (custom_ai,),
            )
            conn.commit()
            return cursor.lastrowid

    def get_chat_ai(self, chat_ai_id):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM chat_ai WHERE id = ?
                """,
                (chat_ai_id,),
            )
            return cursor.fetchone()

    def create_brain_history_chat(self, chat_ai_id, role, content):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO brain_history_chat (chat_ai_id, role, content) VALUES (?, ?, ?)
                """,
                (
                    chat_ai_id,
                    role,
                    content,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_brain_history_chat(self, chat_ai_id):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM brain_history_chat WHERE chat_ai_id = ?
                """,
                (chat_ai_id,),
            )
            return cursor.fetchall()
