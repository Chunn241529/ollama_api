import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List, Optional
from services.repository.db.db_client import create_database_client

# Tên database chính
db_name = "server.sqlite3"

# Database service
def get_db_cursor():
    conn = sqlite3.connect(db_name)
    return conn, conn.cursor()


# Password service (sử dụng Werkzeug)
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


def get_password_by_username_or_email(identifier: str) -> Optional[tuple]:
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


def get_user_by_email(identifier: str) -> Optional[tuple]:
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM user_profile
            WHERE email = ?
            """,
            (identifier,),
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
