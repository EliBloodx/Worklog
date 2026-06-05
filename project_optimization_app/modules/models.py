from dataclasses import dataclass


@dataclass
class Registro:
	id: int | None
	fecha: str
	actividad: str
	descripcion: str
	hora_inicio: str
	hora_fin: str
	horas_totales: float
