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
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_registros_fecha ON registros (fecha);
CREATE INDEX IF NOT EXISTS idx_registros_actividad ON registros (actividad);
CREATE INDEX IF NOT EXISTS idx_registros_estado ON registros (estado);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
