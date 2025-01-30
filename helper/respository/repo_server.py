import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List, Optional

# Tên database chính
db_name = "server.sqlite3"


def create_database_client(db_name):
    # Đường dẫn đến file database
    db_file = f"ui/storage/database_client/{db_name}"

    # Kiểm tra nếu file database tồn tại
    if os.path.exists(db_file):
        return f"Database '{db_name}' đã tồn tại. Không cần tạo mới."

    # Kết nối đến cơ sở dữ liệu SQLite (hoặc tạo mới nếu chưa có)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Tạo bảng chat_ai
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_ai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            custom_ai TEXT,             
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Tạo bảng brain_history_chat
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS brain_history_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_ai_id INTEGER,  -- Khóa ngoại tham chiếu đến bảng chat_ai
            role TEXT,         
            content TEXT,      
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_ai_id) REFERENCES chat_ai (id)
        )
        """
    )

    # Lưu thay đổi và đóng kết nối
    conn.commit()
    conn.close()

    return os.path.join(db_file).replace("\\", "/")


# Database helper
def get_db_cursor():
    conn = sqlite3.connect(db_name)
    return conn, conn.cursor()


# Password helper (sử dụng Werkzeug)
def hash_password(password: str) -> str:
    return generate_password_hash(password)  # Sử dụng phương thức mặc định


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)


def add_user(user_data: dict):
    # Tạo db_name từ username
    db_name = f"{user_data['username']}.sqlite3"
    db_file = create_database_client(db_name)

    conn, cursor = get_db_cursor()
    try:
        # Kiểm tra username hoặc email đã tồn tại
        if is_username_or_email_exists(user_data["username"], user_data["email"]):
            raise ValueError("Username or email already exists.")

        # Hash password
        hashed_password = hash_password(user_data["password"])

        # Insert user vào bảng user
        cursor.execute(
            """
            INSERT INTO user (username, password, verify_code, phone, email, db_name)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_data["username"],
                hashed_password,
                user_data["verify_code"],
                user_data["phone"],
                user_data["email"],
                db_file,
            ),
        )
        user_id = cursor.lastrowid

        # Insert user profile vào bảng user_profile
        cursor.execute(
            """
            INSERT INTO user_profile (user_id, full_name, email, avatar, phone, db_name)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                user_data["full_name"],
                user_data["email"],
                user_data["avatar"],
                user_data["phone"],
                db_file,
            ),
        )

        # Tạo database riêng cho user

        conn.commit()
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Database Error: {e}")
    finally:
        conn.close()


def get_user_by_username_or_email(identifier: str) -> Optional[tuple]:
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            """
            SELECT password FROM user
            WHERE username = ? OR email = ?
            """,
            (identifier, identifier),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_db_user_by_username_or_email(identifier: str) -> Optional[tuple]:
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            """
            SELECT db_name FROM user
            WHERE username = ? OR email = ?
            """,
            (identifier, identifier),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_all_users() -> List[tuple]:
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            """
            SELECT u.id, u.username, u.email, up.full_name, up.avatar, up.db_name
            FROM user u
            LEFT JOIN user_profile up ON u.id = up.user_id
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()


def delete_user(username: str):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("DELETE FROM user WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()


def is_username_or_email_exists(username: str, email: str) -> bool:
    """
    Check if a username or email already exists in the database.
    """
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) FROM user
            WHERE username = ? OR email = ?
            """,
            (username, email),
        )
        result = cursor.fetchone()
        return result[0] > 0  # True nếu tồn tại
    finally:
        conn.close()
