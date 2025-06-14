import os
import sqlite3


def create_database_server(db_name):
    db_file = db_name
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"File '{db_file}' has been deleted.")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            verify_code TEXT,
            phone TEXT,
            email TEXT,
            db_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            email TEXT,
            avatar BLOB,
            phone TEXT,
            db_name TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE INDEX idx_user_username ON user (username);
        CREATE INDEX idx_user_profile_user_id ON user_profile (user_id);
        """
    )

    conn.commit()
    conn.close()

    print("Database created successfully!!!")


create_database_server("server.sqlite3")
