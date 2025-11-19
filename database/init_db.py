from .connection import get_conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            birthdate TEXT,
            role TEXT,
            utec TEXT,
            email TEXT,
            phone TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            remind_at TEXT,
            sent INTEGER DEFAULT 0,
            channel TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sent_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            reminder_id INTEGER,
            sent_at TEXT,
            channel TEXT,
            success INTEGER,
            details TEXT
        )
    ''')

    conn.commit()
    conn.close()