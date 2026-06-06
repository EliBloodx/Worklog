import sqlite3

from werkzeug.security import generate_password_hash

from config import ADMIN_PASSWORD, ADMIN_USERNAME, DATABASE_PATH


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT '',
    proyecto_equipo TEXT NOT NULL DEFAULT '',
    cliente_referencia TEXT NOT NULL DEFAULT '',
    actividad TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    descripcion TEXT DEFAULT '',
    hora_inicio TEXT NOT NULL,
    hora_fin TEXT NOT NULL,
    horas_totales REAL NOT NULL CHECK (horas_totales >= 0),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1))
);

CREATE TABLE IF NOT EXISTS activity_categories (
    category_key TEXT PRIMARY KEY,
    label TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS activity_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_key TEXT NOT NULL,
    option_name TEXT NOT NULL,
    UNIQUE(category_key, option_name),
    FOREIGN KEY (category_key) REFERENCES activity_categories (category_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS record_states (
    state_value TEXT PRIMARY KEY,
    label TEXT NOT NULL UNIQUE
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
            admin_id = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (ADMIN_USERNAME,),
            ).fetchone()["id"]
        else:
            admin_id = admin_exists["id"]

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(registros)").fetchall()
        }
        if "estado" not in columns:
            conn.execute(
                "ALTER TABLE registros ADD COLUMN estado TEXT NOT NULL DEFAULT 'pendiente'"
            )
        if "user_id" not in columns:
            conn.execute(
                "ALTER TABLE registros ADD COLUMN user_id INTEGER"
            )
            conn.execute(
                "UPDATE registros SET user_id = ? WHERE user_id IS NULL",
                (admin_id,),
            )
        if "categoria" not in columns:
            conn.execute(
                "ALTER TABLE registros ADD COLUMN categoria TEXT NOT NULL DEFAULT ''"
            )
        if "proyecto_equipo" not in columns:
            conn.execute(
                "ALTER TABLE registros ADD COLUMN proyecto_equipo TEXT NOT NULL DEFAULT ''"
            )
        if "cliente_referencia" not in columns:
            conn.execute(
                "ALTER TABLE registros ADD COLUMN cliente_referencia TEXT NOT NULL DEFAULT ''"
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_registros_user_id ON registros (user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users(email) WHERE email <> ''"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_options_category ON activity_options (category_key)"
        )

        default_categories = {
            "taller_reparacion": "Taller/Reparacion",
            "programacion": "Programacion",
            "diseno": "Diseno",
            "administracion": "Administracion",
            "produccion_fabricacion": "Produccion/Fabricacion",
        }
        default_activity_options = {
            "taller_reparacion": [
                "Diagnostico",
                "Reparacion mecanica",
                "Reparacion electronica",
                "Mantenimiento preventivo",
                "Mantenimiento correctivo",
                "Calibracion",
                "Ensamblaje/montaje",
                "Pruebas de funcionamiento",
                "Entrega al cliente",
            ],
            "programacion": [
                "Desarrollo de software",
                "Correccion de errores",
                "Automatizacion",
                "Programacion de microcontroladores",
                "Configurar sistemas",
                "Pruebas",
                "Documentacion tecnica",
            ],
            "diseno": [
                "Diseno CAD",
                "Modelado 3D",
                "Diseno de PCB",
                "Diseno de circuitos",
                "Diseno de interfaces",
                "Renderizado",
                "Diseno grafico",
            ],
            "administracion": [
                "Atencion al cliente",
                "Cotizaciones",
                "Compra de materiales",
                "Inventariado",
                "Capacitaciones",
                "Reuniones",
                "Organizacion del taller",
                "Registro rapido",
            ],
            "produccion_fabricacion": [
                "Corte",
                "Impresion 3D",
                "CNC/Laser",
                "Pintura",
                "Acabado",
                "Empaquetado",
            ],
        }
        default_states = {
            "pendiente": "Pendiente",
            "en_progreso": "En progreso",
            "completado": "Completado",
        }

        for category_key, label in default_categories.items():
            conn.execute(
                "INSERT OR IGNORE INTO activity_categories (category_key, label) VALUES (?, ?)",
                (category_key, label),
            )

        for category_key, options in default_activity_options.items():
            for option in options:
                conn.execute(
                    "INSERT OR IGNORE INTO activity_options (category_key, option_name) VALUES (?, ?)",
                    (category_key, option),
                )

        for state_value, label in default_states.items():
            conn.execute(
                "INSERT OR IGNORE INTO record_states (state_value, label) VALUES (?, ?)",
                (state_value, label),
            )

        # Migrate legacy quick-register values to the regular pending workflow.
        conn.execute(
            """
            UPDATE registros
            SET categoria = 'administracion',
                proyecto_equipo = 'Registro rapido',
                actividad = 'Registro rapido',
                estado = 'pendiente'
            WHERE categoria = 'registro_rapido_imcompleto'
               OR estado = 'registro_rapido'
            """
        )
        conn.execute(
            "DELETE FROM activity_options WHERE category_key = 'registro_rapido_imcompleto'"
        )
        conn.execute(
            "DELETE FROM activity_categories WHERE category_key = 'registro_rapido_imcompleto'"
        )
        conn.execute(
            "DELETE FROM record_states WHERE state_value = 'registro_rapido'"
        )
