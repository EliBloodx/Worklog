from dataclasses import dataclass
import re

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from modules.database import connect_db


@dataclass
class User(UserMixin):
    id: int
    username: str
    full_name: str
    email: str
    password_hash: str
    is_admin: bool


def _row_to_user(row) -> User | None:
    if not row:
        return None

    return User(
        id=row["id"],
        username=row["username"],
        full_name=row["full_name"],
        email=row["email"],
        password_hash=row["password_hash"],
        is_admin=bool(row["is_admin"]),
    )


def get_user_by_id(user_id: int) -> User | None:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, email, password_hash, is_admin FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return _row_to_user(row)


def get_user_by_username(username: str) -> User | None:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, email, password_hash, is_admin FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return _row_to_user(row)


def get_user_by_email(email: str) -> User | None:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, email, password_hash, is_admin FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        return _row_to_user(row)


def authenticate_user(username: str, password: str) -> User | None:
    user = get_user_by_username(username.strip())
    if not user:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    return user


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register_user(username: str, password: str, full_name: str, email: str) -> None:
    normalized_username = username.strip().lower()
    normalized_full_name = full_name.strip()
    normalized_email = email.strip().lower()

    if len(normalized_username) < 3:
        raise ValueError("El usuario debe tener al menos 3 caracteres")
    if len(normalized_full_name) < 3:
        raise ValueError("El nombre de usuario debe tener al menos 3 caracteres")
    if len(password) < 8:
        raise ValueError("La contrasena debe tener al menos 8 caracteres")
    if not _EMAIL_PATTERN.fullmatch(normalized_email):
        raise ValueError("El correo electronico no es valido")

    if get_user_by_username(normalized_username):
        raise ValueError("Ese usuario ya existe")
    if get_user_by_email(normalized_email):
        raise ValueError("Ese correo electronico ya esta registrado")

    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO users (username, full_name, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?, 0)
            """,
            (
                normalized_username,
                normalized_full_name,
                normalized_email,
                generate_password_hash(password),
            ),
        )
