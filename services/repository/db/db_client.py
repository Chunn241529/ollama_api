import os
import sqlite3



def create_database_client(db_name):
    # Đường dẫn đến file database
    db_file = f"storage/database_client/{db_name}"

    # Kiểm tra nếu file database tồn tại
    if os.path.exists(db_file):
        return f"Database '{db_name}' đã tồn tại. Không cần tạo mới."

    # Kết nối đến cơ sở dữ liệu SQLite (hoặc tạo mới nếu chưa có)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Tạo bảng chat
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            custom_ai TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Tạo bảng brain_history_chat
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_ai_id INTEGER,
            role TEXT,
            content TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_ai_id) REFERENCES chat (id)
        )
        """
    )

    # Lưu thay đổi và đóng kết nối
    conn.commit()
    conn.close()

    return os.path.join(db_file).replace("\\", "/")
