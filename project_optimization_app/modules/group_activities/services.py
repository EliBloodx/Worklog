from __future__ import annotations

from datetime import datetime

from modules.group_activities.repository import (
    close_group_activity,
    create_group_activity_record,
    get_group_activities_for_admin,
    get_group_activities_for_user,
    insert_group_activity,
)
from modules.records import get_activity_catalog


def normalize_group_activity_form(form_data: dict[str, str]) -> dict[str, str]:
    catalog = get_activity_catalog()

    fecha = form_data.get("fecha", "").strip()
    fecha_estimada = form_data.get("fecha_estimada", "").strip()
    categoria = form_data.get("categoria", "").strip()
    actividad = form_data.get("actividad", "").strip()
    identificador_interno = form_data.get("identificador_interno", "").strip()
    descripcion = form_data.get("descripcion", "").strip()

    if not fecha:
        raise ValueError("La fecha es obligatoria")
    if not fecha_estimada:
        raise ValueError("La fecha estimada es obligatoria")
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        datetime.strptime(fecha_estimada, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Las fechas deben tener el formato YYYY-MM-DD") from exc
    if not categoria:
        raise ValueError("La categoria es obligatoria")
    if categoria not in catalog:
        raise ValueError("La categoria seleccionada no es valida")
    if not actividad:
        raise ValueError("La actividad es obligatoria")
    if actividad not in catalog[categoria]["project_options"]:
        raise ValueError("La actividad seleccionada no pertenece a la categoria")
    if not identificador_interno:
        raise ValueError("El identificador interno es obligatorio")
    if not descripcion:
        raise ValueError("La descripcion es obligatoria")

    return {
        "fecha": fecha,
        "fecha_estimada": fecha_estimada,
        "categoria": categoria,
        "actividad": actividad,
        "identificador_interno": identificador_interno,
        "descripcion": descripcion,
        "estado": "en_progreso",
    }


def build_user_group_activities_context(user_id: int) -> dict[str, object]:
    activity_catalog = get_activity_catalog()
    group_activities = []
    for activity in get_group_activities_for_user(user_id):
        group_activities.append(
            {
                **dict(activity),
                "categoria_label": activity_catalog.get(activity["categoria"], {}).get("label", activity["categoria"]),
            }
        )
    return {
        "group_activities": group_activities,
    }


def build_admin_group_activities_context() -> dict[str, object]:
    activity_catalog = get_activity_catalog()
    group_activities = []
    for activity in get_group_activities_for_admin():
        group_activities.append(
            {
                **dict(activity),
                "categoria_label": activity_catalog.get(activity["categoria"], {}).get("label", activity["categoria"]),
            }
        )
    return {
        "group_activities": group_activities,
        "activity_catalog": activity_catalog,
    }


def create_group_activity(form_data: dict[str, str], creator_user_id: int) -> tuple[bool, str]:
    normalized = normalize_group_activity_form(form_data)
    normalized["creator_user_id"] = creator_user_id
    insert_group_activity(normalized)
    return True, "Actividad grupal creada"


def join_group_activity(activity_id: int, user_id: int) -> tuple[bool, str]:
    return create_group_activity_record(activity_id, user_id)


def close_activity(activity_id: int) -> tuple[bool, str]:
    if close_group_activity(activity_id):
        return True, "Actividad grupal cerrada"
    return False, "No se pudo cerrar la actividad grupal"