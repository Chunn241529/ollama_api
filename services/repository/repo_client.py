import os
import sqlite3
from datetime import datetime


class RepositoryClient:
    def __init__(self, db_path):
        """Khởi tạo repository với đường dẫn đến cơ sở dữ liệu SQLite."""
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Database file '{db_path}' does not exist."
            )  # Ném lỗi nếu file không tồn tại
        self.db_path = db_path

    def _connect(self):
        """Kết nối đến cơ sở dữ liệu."""
        return sqlite3.connect(self.db_path)

    # =============================== TABLE: chat_ai ===============================

    def insert_chat_ai(self, name, custom_ai):
        """Thêm một bản ghi vào bảng chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat (name, custom_ai, updated_at)
                VALUES (?, ?, ?)
                """,
                (name, custom_ai, datetime.now()),
            )
            conn.commit()
            return cursor.lastrowid

    def get_chat(self):
        """Lấy tất cả bản ghi từ bảng chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat")
            return cursor.fetchall()

    def get_chat_by_id(self, chat_ai_id):
        """Lấy bản ghi từ bảng chat theo id."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat WHERE id = ?",
                (chat_ai_id,),
            )
            return cursor.fetchone()

    def get_custom_chat_ai_by_id(self, chat_ai_id):
        """Lấy custom_ai từ bảng chat theo id."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT custom_ai FROM chat WHERE id = ?",
                (chat_ai_id,),
            )
            return cursor.fetchone()

    # =============================== TABLE: brain_history_chat ===============================

    def insert_brain_history_chat(self, chat_ai_id, role, content):
        """Thêm một bản ghi vào bảng history_chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO history_chat (chat_ai_id, role, content, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_ai_id, role, content, datetime.now()),
            )
            conn.commit()

    def get_history_chat(self):
        """Lấy tất cả bản ghi từ bảng history_chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history_chat")
            return cursor.fetchall()

    def get_history_chat_by_role(self, role):
        """Lấy tất cả bản ghi từ bảng history_chat theo role."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM history_chat WHERE role = ?",
                (role,),
            )
            return cursor.fetchall()

    def get_history_chat_by_chat_ai_id(self, chat_ai_id):
        """Lấy tất cả bản ghi từ bảng history_chat theo chat_ai_id."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role,content FROM history_chat WHERE chat_ai_id = ?",
                (chat_ai_id,),
            )
            return cursor.fetchall()

    def get_latest_history_chat(self):
        """Lấy tất cả bản ghi từ bảng history_chat có chat_ai_id lớn nhất."""
        with self._connect() as conn:
            cursor = conn.cursor()
            # Lấy chat_ai_id lớn nhất
            cursor.execute("SELECT MAX(chat_ai_id) FROM history_chat")
            max_chat_ai_id = cursor.fetchone()[0]

            if max_chat_ai_id is None:
                return []  # Không có bản ghi nào

            # Lấy tất cả các bản ghi với chat_ai_id lớn nhất
            cursor.execute(
                "SELECT * FROM history_chat WHERE chat_ai_id = ?",
                (max_chat_ai_id,),
            )
            return cursor.fetchall()

    # =============================== UPDATE AND DELETE ===============================

    def update_chat(self, chat_ai_id, name, custom_ai):
        """Cập nhật thông tin trong bảng chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE chat
                SET name = ?, custom_ai = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, custom_ai, datetime.now(), chat_ai_id),
            )
            conn.commit()

    def delete_chat(self, chat_ai_id):
        """Xóa bản ghi từ bảng chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat WHERE id = ?", (chat_ai_id,))
            conn.commit()

    def delete_history_chat(self, chat_id):
        """Xóa bản ghi từ bảng history_chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history_chat WHERE id = ?", (chat_id,))
            conn.commit()

    def delete_all_history_chat(self):
        """Xóa tất cả bản ghi từ bảng history_chat."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history_chat")
            conn.commit()
