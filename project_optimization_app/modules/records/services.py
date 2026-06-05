from datetime import datetime
import io
import re

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill


_TIME_HHMM_PATTERN = re.compile(r"^\d{2}:\d{2}$")
VALID_STATES = {"pendiente", "en_progreso", "completado"}


def _parse_hhmm(value: str, field_name: str) -> datetime:
    raw_value = value.strip()
    if not _TIME_HHMM_PATTERN.fullmatch(raw_value):
        raise ValueError(f"{field_name} debe tener el formato HH:MM")

    try:
        return datetime.strptime(raw_value, "%H:%M")
    except ValueError as exc:
        raise ValueError(f"{field_name} no es una hora valida") from exc


def calculate_worked_hours(hora_inicio: str, hora_fin: str, precision: int = 2) -> float:
    start = _parse_hhmm(hora_inicio, "hora_inicio")
    end = _parse_hhmm(hora_fin, "hora_fin")

    if end <= start:
        raise ValueError("La hora de fin debe ser mayor que la hora de inicio")

    diff_hours = (end - start).total_seconds() / 3600
    return round(diff_hours, precision)


def calculate_hours(hora_inicio: str, hora_fin: str) -> float:
    return calculate_worked_hours(hora_inicio, hora_fin)


_ESTADO_LABELS = {
    "pendiente": "Pendiente",
    "en_progreso": "En progreso",
    "completado": "Completado",
}

_HEADER_FILL = PatternFill("solid", fgColor="1D4ED8")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_TOTAL_FILL = PatternFill("solid", fgColor="DBEAFE")
_TOTAL_FONT = Font(bold=True)


def build_excel(registros, total_horas: float) -> bytes:
    rows = [
        {
            "Fecha": r["fecha"],
            "Actividad": r["actividad"],
            "Estado": _ESTADO_LABELS.get(r["estado"], r["estado"]),
            "Descripcion": r["descripcion"],
            "Hora inicio": r["hora_inicio"],
            "Hora fin": r["hora_fin"],
            "Horas totales": round(float(r["horas_totales"]), 2),
        }
        for r in registros
    ]

    df = pd.DataFrame(rows)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Registros", index=False, startrow=0)
        ws = writer.sheets["Registros"]

        for col_idx, _ in enumerate(df.columns, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = _HEADER_FILL
            cell.font = _HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for col in ws.columns:
            max_len = max(
                len(str(cell.value)) if cell.value is not None else 0
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = max(max_len + 4, 12)

        total_row = len(df) + 2
        ws.cell(row=total_row, column=6).value = "TOTAL"
        ws.cell(row=total_row, column=6).font = _TOTAL_FONT
        ws.cell(row=total_row, column=7).value = round(total_horas, 2)
        ws.cell(row=total_row, column=7).font = _TOTAL_FONT
        for col_idx in range(6, 8):
            ws.cell(row=total_row, column=col_idx).fill = _TOTAL_FILL

    return output.getvalue()


def normalize_form_data(form_data: dict[str, str]) -> dict[str, str | float]:
    required = ["fecha", "actividad", "hora_inicio", "hora_fin"]
    for field in required:
        if not form_data.get(field):
            raise ValueError(f"El campo '{field}' es obligatorio")

    actividad = form_data["actividad"].strip()
    if not actividad:
        raise ValueError("La actividad no puede estar vacia")

    estado = form_data.get("estado", "pendiente").strip().lower()
    if estado not in VALID_STATES:
        raise ValueError("El estado no es valido")

    try:
        datetime.strptime(form_data["fecha"], "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("La fecha debe tener el formato YYYY-MM-DD") from exc

    try:
        datetime.strptime(form_data["hora_inicio"], "%H:%M")
        datetime.strptime(form_data["hora_fin"], "%H:%M")
    except ValueError as exc:
        raise ValueError("Las horas deben tener el formato HH:MM") from exc

    hours = calculate_hours(form_data["hora_inicio"], form_data["hora_fin"])
    return {
        "fecha": form_data["fecha"],
        "actividad": actividad,
        "estado": estado,
        "descripcion": form_data.get("descripcion", "").strip(),
        "hora_inicio": form_data["hora_inicio"],
        "hora_fin": form_data["hora_fin"],
        "horas_totales": hours,
    }
