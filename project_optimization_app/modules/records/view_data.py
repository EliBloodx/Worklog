from collections.abc import Mapping
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
    return {
        field: str(values.get(field, "") or "").strip()
        for field in FILTER_FIELDS
    }


def build_records_page_context(filters: RecordFilters) -> dict[str, object]:
    registros = list_records(**filters)
    total = total_hours(**filters)
    return {
        "registros": registros,
        "total_horas": total,
        "filtros": filters,
    }


def build_reports_page_context(filters: RecordFilters) -> dict[str, object]:
    registros = list_records(**filters)
    total = total_hours(**filters)
    frecuentes = top_activities(**filters, limit=5)
    recientes = recent_records(**filters, limit=6)
    por_categoria = hours_by_category(**filters, limit=6)
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
    }
