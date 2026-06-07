from __future__ import annotations

from datetime import datetime
from typing import Any

from modules.database import connect_db


def insert_group_activity(data: dict[str, Any]) -> int:
    with connect_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO group_activities (
                creator_user_id,
                fecha,
                fecha_estimada,
                categoria,
                actividad,
                identificador_interno,
                descripcion,
                estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["creator_user_id"],
                data["fecha"],
                data["fecha_estimada"],
                data["categoria"],
                data["actividad"],
                data["identificador_interno"],
                data["descripcion"],
                data.get("estado", "en_progreso"),
            ),
        )
        return int(cursor.lastrowid)


def get_group_activity_by_id(activity_id: int):
    query = """
        SELECT
            ga.*,
            COALESCE(COUNT(DISTINCT r.id), 0) AS participant_count,
            COALESCE(SUM(CASE WHEN COALESCE(r.hora_fin, '') <> '' THEN r.horas_totales ELSE 0 END), 0) AS total_hours
        FROM group_activities ga
        LEFT JOIN registros r ON r.group_activity_id = ga.id
        WHERE ga.id = ?
        GROUP BY ga.id
    """
    with connect_db() as conn:
        return conn.execute(query, (activity_id,)).fetchone()


def get_group_activities_for_admin():
    query = """
        SELECT
            ga.*,
            COALESCE(COUNT(DISTINCT r.id), 0) AS participant_count,
            COALESCE(SUM(CASE WHEN COALESCE(r.hora_fin, '') <> '' THEN r.horas_totales ELSE 0 END), 0) AS total_hours
        FROM group_activities ga
        LEFT JOIN registros r ON r.group_activity_id = ga.id
        GROUP BY ga.id
        ORDER BY ga.estado ASC, ga.fecha DESC, ga.id DESC
    """
    with connect_db() as conn:
        return conn.execute(query).fetchall()


def get_group_activities_for_user(user_id: int):
    query = """
        SELECT
            ga.*,
            COALESCE(COUNT(DISTINCT r.id), 0) AS participant_count,
            COALESCE(SUM(CASE WHEN COALESCE(r.hora_fin, '') <> '' THEN r.horas_totales ELSE 0 END), 0) AS total_hours,
            EXISTS(
                SELECT 1
                FROM registros r2
                WHERE r2.group_activity_id = ga.id
                  AND r2.user_id = ?
            ) AS joined_by_user
        FROM group_activities ga
        LEFT JOIN registros r ON r.group_activity_id = ga.id
        WHERE ga.estado = 'en_progreso'
        GROUP BY ga.id
        ORDER BY ga.fecha ASC, ga.id DESC
    """
    with connect_db() as conn:
        return conn.execute(query, (user_id,)).fetchall()


def close_group_activity(activity_id: int) -> bool:
    with connect_db() as conn:
        cursor = conn.execute(
            """
            UPDATE group_activities
            SET estado = 'completado',
                closed_at = ?
            WHERE id = ?
              AND estado = 'en_progreso'
            """,
            (datetime.now().isoformat(timespec="seconds"), activity_id),
        )
        return cursor.rowcount > 0


def create_group_activity_record(activity_id: int, user_id: int) -> tuple[bool, str]:
    activity = get_group_activity_by_id(activity_id)
    if not activity:
        return False, "La actividad grupal no existe"
    if activity["estado"] != "en_progreso":
        return False, "La actividad grupal ya fue cerrada"

    with connect_db() as conn:
        already_joined = conn.execute(
            """
            SELECT 1
            FROM registros
            WHERE group_activity_id = ?
              AND user_id = ?
            """,
            (activity_id, user_id),
        ).fetchone()
        if already_joined:
            return False, "Ya te uniste a esta actividad grupal"

        conn.execute(
            """
            INSERT INTO registros (
                user_id,
                fecha,
                fecha_estimada,
                categoria,
                proyecto_equipo,
                cliente_referencia,
                actividad,
                estado,
                descripcion,
                hora_inicio,
                hora_fin,
                horas_totales,
                group_activity_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                activity["fecha"],
                activity["fecha_estimada"],
                activity["categoria"],
                activity["actividad"],
                activity["identificador_interno"],
                activity["actividad"],
                "en_progreso",
                "",
                datetime.now().strftime("%H:%M"),
                "",
                0.0,
                activity_id,
            ),
        )
    return True, "Te uniste a la actividad grupal. Completa la hora de fin en tus registros."