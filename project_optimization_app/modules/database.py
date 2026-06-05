import sqlite3

from werkzeug.security import generate_password_hash

from config import ADMIN_PASSWORD, ADMIN_USERNAME, DATABASE_PATH


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    actividad TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    descripcion TEXT DEFAULT '',
    hora_inicio TEXT NOT NULL,
    hora_fin TEXT NOT NULL,
    horas_totales REAL NOT NULL CHECK (horas_totales >= 0)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1))
);
"""


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect_db() as conn:
        conn.executescript(SCHEMA_SQL)

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(registros)").fetchall()
        }
        if "estado" not in columns:
            conn.execute(
                "ALTER TABLE registros ADD COLUMN estado TEXT NOT NULL DEFAULT 'pendiente'"
            )

        user_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "is_admin" not in user_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1))"
            )
        if "full_name" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''")
        if "email" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''")

        admin_exists = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (ADMIN_USERNAME,),
        ).fetchone()
        if not admin_exists:
            conn.execute(
                "INSERT INTO users (username, full_name, email, password_hash, is_admin) VALUES (?, ?, ?, ?, 1)",
                (
                    ADMIN_USERNAME,
                    "Administrador",
                    f"{ADMIN_USERNAME}@local",
                    generate_password_hash(ADMIN_PASSWORD),
                ),
            )

        conn.execute(
            "UPDATE users SET full_name = 'Administrador' WHERE username = ? AND COALESCE(full_name, '') = ''",
            (ADMIN_USERNAME,),
        )
        conn.execute(
            "UPDATE users SET email = ? WHERE username = ? AND COALESCE(email, '') = ''",
            (f"{ADMIN_USERNAME}@local", ADMIN_USERNAME),
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_registros_fecha ON registros (fecha)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_registros_actividad ON registros (actividad)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_registros_estado ON registros (estado)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users(email) WHERE email <> ''"
        )
