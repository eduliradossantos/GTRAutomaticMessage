from .connection import get_conn
from .init_db import init_db # Para garantir que a tabela de locais seja inicializada, se necessário

def add_user(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (name, birthdate, role, utec, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get('name'),
        data.get('birthdate'),
        data.get('role'),
        data.get('utec'),
        data.get('email'),
        data.get('phone'),
    ))
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_user(user_id, data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE users SET
            name = ?, birthdate = ?, role = ?, utec = ?, email = ?, phone = ?
        WHERE id = ?
    """, (
        data.get('name'),
        data.get('birthdate'),
        data.get('role'),
        data.get('utec'),
        data.get('email'),
        data.get('phone'),
        user_id
    ))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def list_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows

def list_utecs():
    # Lista inicial de UTECs (com prefixo "UTEC")
    initial_utecs = [
        "UTEC ALTO SANTA TEREZINHA", "UTEC BOA VIAGEM", "UTEC CAXANGÁ", "UTEC COQUE", "UTEC CORDEIRO",
        "UTEC CRISTIANO DONATO", "UTEC PINA", "UTEC GREGÓRIO BEZERRA", "UTEC IBURA", "UTEC JARDIM BOTÂNICO",
        "UTEC LARGO DOM LUÍS", "UTEC NOVA DESCOBERTA", "UTEC SANTO AMARO", "UTEC SÍTIO TRINDADE"
    ]
    
    # Adiciona locais únicos que não estão na lista inicial, extraindo dos usuários
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT utec FROM users WHERE utec IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    
    unique_utecs = set(initial_utecs)
    for row in rows:
        if row['utec'] and row['utec'] not in unique_utecs:
            unique_utecs.add(row['utec'])
            
    return sorted(list(unique_utecs))

def get_users_by_utec(utec):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE utec = ? ORDER BY name", (utec,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_users_ids():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    rows = c.fetchall()
    conn.close()
    return [row['id'] for row in rows]

def get_users_by_role(role):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE role = ? ORDER BY name", (role,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_roles():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT role FROM users WHERE role IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    
    initial_roles = ["Professor Multiplicador", "Coordenador", "Outro"]
    unique_roles = set(initial_roles)
    for row in rows:
        if row['role'] and row['role'] not in unique_roles:
            unique_roles.add(row['role'])
            
    return sorted(list(unique_roles))


def add_reminder(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO reminders (user_id, title, description, remind_at, channel)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get('user_id'),
        data.get('title'),
        data.get('description'),
        data.get('remind_at'),
        data.get('channel'),
    ))
    conn.commit()
    conn.close()


def get_reminder_by_id(reminder_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_reminder(reminder_id, data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE reminders SET
            user_id = ?, title = ?, description = ?, remind_at = ?, channel = ?
        WHERE id = ?
    """, (
        data.get('user_id'),
        data.get('title'),
        data.get('description'),
        data.get('remind_at'),
        data.get('channel'),
        reminder_id
    ))
    conn.commit()
    conn.close()

def delete_reminder(reminder_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def list_reminders():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT r.*, u.name AS user_name
        FROM reminders r
        LEFT JOIN users u ON r.user_id = u.id
        ORDER BY remind_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def list_utecs():
    # Lista inicial de UTECs (com prefixo "UTEC")
    initial_utecs = [
        "UTEC ALTO SANTA TEREZINHA", "UTEC BOA VIAGEM", "UTEC CAXANGÁ", "UTEC COQUE", "UTEC CORDEIRO",
        "UTEC CRISTIANO DONATO", "UTEC PINA", "UTEC GREGÓRIO BEZERRA", "UTEC IBURA", "UTEC JARDIM BOTÂNICO",
        "UTEC LARGO DOM LUÍS", "UTEC NOVA DESCOBERTA", "UTEC SANTO AMARO", "UTEC SÍTIO TRINDADE"
    ]
    
    # Adiciona locais únicos que não estão na lista inicial, extraindo dos usuários
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT utec FROM users WHERE utec IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    
    unique_utecs = set(initial_utecs)
    for row in rows:
        if row['utec'] and row['utec'] not in unique_utecs:
            unique_utecs.add(row['utec'])
            
    return sorted(list(unique_utecs))

def get_users_by_utec(utec):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE utec = ? ORDER BY name", (utec,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_users_ids():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    rows = c.fetchall()
    conn.close()
    return [row['id'] for row in rows]

def get_users_by_role(role):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE role = ? ORDER BY name", (role,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_roles():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT role FROM users WHERE role IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    
    initial_roles = ["Professor Multiplicador", "Coordenador", "Outro"]
    unique_roles = set(initial_roles)
    for row in rows:
        if row['role'] and row['role'] not in unique_roles:
            unique_roles.add(row['role'])
            
    return sorted(list(unique_roles))
