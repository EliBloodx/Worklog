from typing import Any

from modules.database import connect_db


def _build_filters(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    user_id: int | None = None,
) -> tuple[str, list[Any]]:
    clause = "WHERE 1=1"
    params: list[Any] = []

    if user_id is not None:
        clause += " AND r.user_id = ?"
        params.append(user_id)

    if fecha:
        clause += " AND fecha = ?"
        params.append(fecha)
    else:
        if fecha_desde:
            clause += " AND fecha >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            clause += " AND fecha <= ?"
            params.append(fecha_hasta)

    if actividad:
        clause += " AND actividad LIKE ?"
        params.append(f"%{actividad}%")

    if estado:
        clause += " AND estado = ?"
        params.append(estado)

    return clause, params


def insert_record(data: dict[str, Any]) -> None:
    with connect_db() as conn:
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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["user_id"],
                data["fecha"],
                data.get("fecha_estimada") or "",
                data["categoria"],
                data["proyecto_equipo"],
                data["cliente_referencia"],
                data["actividad"],
                data["estado"],
                data.get("descripcion", ""),
                data["hora_inicio"],
                data["hora_fin"],
                data["horas_totales"],
                data.get("group_activity_id"),
            ),
        )


def update_record(record_id: int, data: dict[str, Any]) -> bool:
    with connect_db() as conn:
        cursor = conn.execute(
            """
            UPDATE registros
            SET fecha = ?,
                fecha_estimada = COALESCE(?, fecha_estimada),
                categoria = ?,
                proyecto_equipo = ?,
                cliente_referencia = ?,
                actividad = ?,
                estado = ?,
                descripcion = ?,
                hora_inicio = ?,
                hora_fin = ?,
                horas_totales = ?
            WHERE id = ?
            """,
            (
                data["fecha"],
                data.get("fecha_estimada") or None,
                data["categoria"],
                data["proyecto_equipo"],
                data["cliente_referencia"],
                data["actividad"],
                data["estado"],
                data.get("descripcion", ""),
                data["hora_inicio"],
                data["hora_fin"],
                data["horas_totales"],
                record_id,
            ),
        )
        return cursor.rowcount > 0


def delete_record(record_id: int) -> bool:
    with connect_db() as conn:
        cursor = conn.execute("DELETE FROM registros WHERE id = ?", (record_id,))
        return cursor.rowcount > 0


def get_record_by_id(record_id: int):
    with connect_db() as conn:
        return conn.execute(
            """
            SELECT r.*, u.username AS owner_username, u.full_name AS owner_full_name
            FROM registros r
            JOIN users u ON u.id = r.user_id
            WHERE r.id = ?
            """,
            (record_id,),
        ).fetchone()


def list_records(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    user_id: int | None = None,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
        user_id=user_id,
    )
    query = f"""
        SELECT r.*, u.username AS owner_username, u.full_name AS owner_full_name
        FROM registros r
        JOIN users u ON u.id = r.user_id
        {where_clause}
    """
    query += " ORDER BY fecha DESC, hora_inicio DESC"

    with connect_db() as conn:
        return conn.execute(query, params).fetchall()


def total_hours(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    user_id: int | None = None,
) -> float:
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
        user_id=user_id,
    )
    query = f"SELECT COALESCE(SUM(r.horas_totales), 0) AS total FROM registros r {where_clause}"

    with connect_db() as conn:
        row = conn.execute(query, params).fetchone()
        return float(row["total"])


def top_activities(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    user_id: int | None = None,
    limit: int = 5,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
        user_id=user_id,
    )
    query = f"""
        SELECT actividad,
               COUNT(*) AS veces,
               COALESCE(SUM(horas_totales), 0) AS horas
        FROM registros r
        {where_clause}
        GROUP BY r.actividad
        ORDER BY veces DESC, horas DESC, actividad ASC
        LIMIT ?
    """

    with connect_db() as conn:
        return conn.execute(query, [*params, limit]).fetchall()


def recent_records(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    user_id: int | None = None,
    limit: int = 6,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
        user_id=user_id,
    )
    query = f"""
        SELECT r.*, u.username AS owner_username, u.full_name AS owner_full_name
        FROM registros r
        JOIN users u ON u.id = r.user_id
        {where_clause}
        ORDER BY r.fecha DESC, r.hora_inicio DESC, r.id DESC
        LIMIT ?
    """

    with connect_db() as conn:
        return conn.execute(query, [*params, limit]).fetchall()


def hours_by_category(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    user_id: int | None = None,
    limit: int = 6,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
        user_id=user_id,
    )
    category_expr = "CASE WHEN COALESCE(TRIM(r.categoria), '') <> '' THEN r.categoria ELSE 'general' END"
    query = f"""
        SELECT {category_expr} AS categoria,
               COALESCE(SUM(r.horas_totales), 0) AS horas,
               COUNT(*) AS registros
        FROM registros r
        {where_clause}
        GROUP BY categoria
        ORDER BY horas DESC, registros DESC, categoria ASC
        LIMIT ?
    """

    with connect_db() as conn:
        return conn.execute(query, [*params, limit]).fetchall()


def get_users_summary():
    query = """
        SELECT
            u.id,
            u.username,
            u.full_name,
            u.email,
            u.is_admin,
            COUNT(r.id) AS total_registros,
            COALESCE(SUM(r.horas_totales), 0) AS total_horas
        FROM users u
        LEFT JOIN registros r ON r.user_id = u.id
        GROUP BY u.id, u.username, u.full_name, u.email, u.is_admin
        ORDER BY u.is_admin DESC, total_horas DESC, u.username ASC
    """

    with connect_db() as conn:
        return conn.execute(query).fetchall()


def count_quick_incomplete_records(user_id: int) -> int:
    query = """
        SELECT COUNT(*) AS total
        FROM registros
        WHERE user_id = ?
                    AND estado = 'en_progreso'
          AND COALESCE(hora_fin, '') = ''
    """

    with connect_db() as conn:
        row = conn.execute(query, (user_id,)).fetchone()
        return int(row["total"])
