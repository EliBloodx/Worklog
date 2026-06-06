from collections.abc import Mapping
import re
from typing import TypedDict

from modules.records.repository import (
    hours_by_category,
    list_records,
    recent_records,
    total_hours,
    top_activities,
)


class RecordFilters(TypedDict):
    fecha: str
    fecha_desde: str
    fecha_hasta: str
    actividad: str
    estado: str


FILTER_FIELDS = ("fecha", "fecha_desde", "fecha_hasta", "actividad", "estado")


def get_record_filters(values: Mapping[str, object]) -> RecordFilters:
    filters = {
        field: str(values.get(field, "") or "").strip()
        for field in FILTER_FIELDS
    }

    # `date_range` supports one-day (exact date) or start/end interval from a single picker.
    raw_date_range = str(values.get("date_range", "") or "").strip()
    if raw_date_range:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", raw_date_range)
        if len(dates) == 1:
            filters["fecha"] = dates[0]
            filters["fecha_desde"] = ""
            filters["fecha_hasta"] = ""
        elif len(dates) >= 2:
            start_date, end_date = dates[0], dates[1]
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            filters["fecha"] = ""
            filters["fecha_desde"] = start_date
            filters["fecha_hasta"] = end_date

    return filters


def build_records_page_context(filters: RecordFilters) -> dict[str, object]:
    registros = list_records(**filters)
    total = total_hours(**filters)
    return {
        "registros": registros,
        "total_horas": total,
        "filtros": filters,
        "subject_user": None,
    }


def build_records_page_context_for_user(
    filters: RecordFilters,
    user_id: int,
    subject_user: object | None = None,
) -> dict[str, object]:
    registros = list_records(**filters, user_id=user_id)
    total = total_hours(**filters, user_id=user_id)
    return {
        "registros": registros,
        "total_horas": total,
        "filtros": filters,
        "subject_user": subject_user,
    }


def build_reports_page_context(
    filters: RecordFilters,
    user_id: int | None = None,
    subject_user: object | None = None,
) -> dict[str, object]:
    registros = list_records(**filters, user_id=user_id)
    total = total_hours(**filters, user_id=user_id)
    frecuentes = top_activities(**filters, user_id=user_id, limit=5)
    recientes = recent_records(**filters, user_id=user_id, limit=6)
    por_categoria = hours_by_category(**filters, user_id=user_id, limit=6)
    total_registros = len(registros)
    promedio = round(total / total_registros, 2) if total_registros else 0.0

    return {
        "registros": registros,
        "total_horas": total,
        "actividades_frecuentes": frecuentes,
        "registros_recientes": recientes,
        "horas_por_categoria": por_categoria,
        "total_registros": total_registros,
        "promedio_horas": promedio,
        "actividades_unicas": len(frecuentes),
        "filtros": filters,
        "subject_user": subject_user,
    }
