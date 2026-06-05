from typing import Any

from modules.database import connect_db


def _build_filters(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
) -> tuple[str, list[Any]]:
    clause = "WHERE 1=1"
    params: list[Any] = []

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
            INSERT INTO registros (fecha, actividad, estado, descripcion, hora_inicio, hora_fin, horas_totales)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["fecha"],
                data["actividad"],
                data["estado"],
                data.get("descripcion", ""),
                data["hora_inicio"],
                data["hora_fin"],
                data["horas_totales"],
            ),
        )


def update_record(record_id: int, data: dict[str, Any]) -> bool:
    with connect_db() as conn:
        cursor = conn.execute(
            """
            UPDATE registros
            SET fecha = ?, actividad = ?, estado = ?, descripcion = ?, hora_inicio = ?, hora_fin = ?, horas_totales = ?
            WHERE id = ?
            """,
            (
                data["fecha"],
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
        return conn.execute("SELECT * FROM registros WHERE id = ?", (record_id,)).fetchone()


def list_records(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
    )
    query = f"SELECT * FROM registros {where_clause}"
    query += " ORDER BY fecha DESC, hora_inicio DESC"

    with connect_db() as conn:
        return conn.execute(query, params).fetchall()


def total_hours(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
) -> float:
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
    )
    query = f"SELECT COALESCE(SUM(horas_totales), 0) AS total FROM registros {where_clause}"

    with connect_db() as conn:
        row = conn.execute(query, params).fetchone()
        return float(row["total"])


def top_activities(
    fecha: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    actividad: str = "",
    estado: str = "",
    limit: int = 5,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
    )
    query = f"""
        SELECT actividad,
               COUNT(*) AS veces,
               COALESCE(SUM(horas_totales), 0) AS horas
        FROM registros
        {where_clause}
        GROUP BY actividad
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
    limit: int = 6,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
    )
    query = f"""
        SELECT *
        FROM registros
        {where_clause}
        ORDER BY fecha DESC, hora_inicio DESC, id DESC
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
    limit: int = 6,
):
    where_clause, params = _build_filters(
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        actividad=actividad,
        estado=estado,
    )
    category_expr = """
        CASE
            WHEN INSTR(actividad, ':') > 0 THEN TRIM(SUBSTR(actividad, 1, INSTR(actividad, ':') - 1))
            WHEN INSTR(actividad, '-') > 0 THEN TRIM(SUBSTR(actividad, 1, INSTR(actividad, '-') - 1))
            ELSE 'General'
        END
    """
    query = f"""
        SELECT {category_expr} AS categoria,
               COALESCE(SUM(horas_totales), 0) AS horas,
               COUNT(*) AS registros
        FROM registros
        {where_clause}
        GROUP BY categoria
        ORDER BY horas DESC, registros DESC, categoria ASC
        LIMIT ?
    """

    with connect_db() as conn:
        return conn.execute(query, [*params, limit]).fetchall()
