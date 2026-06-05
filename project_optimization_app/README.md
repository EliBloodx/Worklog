# Project Optimization App

Sistema web para registro de horas de trabajo construido con Python, Flask, SQLite y Bootstrap 5.

## Funcionalidades

- Crear registros de trabajo
- Registrar horas invertidas por actividad
- Ver historial de registros
- Editar registros existentes
- Eliminar registros
- Filtrar por fecha y actividad
- Ver total de horas trabajadas

## Stack

- Python 3.10+
- Flask
- SQLite
- Bootstrap 5

## Estructura del proyecto

```text
project_optimization_app/
├── app.py
├── config.py
├── database.db
├── requirements.txt
├── modules/
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   ├── repository.py
│   ├── routes.py
│   └── services.py
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── img/
│   └── js/
│       └── app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── registro.html
    └── reportes.html
```

## Arquitectura (resumen)

- `app.py`: inicializa Flask, carga configuración, inicializa base de datos y registra rutas.
- `config.py`: configuración principal de la app (DB y clave secreta).
- `modules/database.py`: conexión e inicialización de tablas SQLite.
- `modules/repository.py`: consultas SQL (CRUD y agregaciones).
- `modules/services.py`: lógica de negocio (validación y cálculo de horas).
- `modules/routes.py`: endpoints HTTP y renderizado de vistas.
- `templates/`: vistas HTML con Jinja2 y Bootstrap.
- `static/`: recursos estáticos (CSS/JS/imagenes).

## Requisitos

Instala dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución local

Desde la carpeta `project_optimization_app`:

```bash
python app.py
```

Luego abre:

```text
http://127.0.0.1:5000
```

Tambien puedes configurar host/puerto con variables de entorno:

```bash
# PowerShell
$env:APP_HOST="127.0.0.1"
$env:APP_PORT="5000"
$env:APP_DEBUG="1"
python app.py
```

Para acceso desde otros dispositivos en tu red local, usa:

```bash
$env:APP_HOST="0.0.0.0"
python app.py
```

## Variables y configuración

En `config.py`:

- `DATABASE_PATH`: ruta del archivo SQLite
- `SECRET_KEY`: clave de sesión de Flask

Para producción, cambia `SECRET_KEY` por una variable de entorno segura.

## Flujo básico de uso

1. Ir a Inicio.
2. Crear un nuevo registro.
3. Revisar historial en la tabla.
4. Editar o eliminar desde acciones.
5. Aplicar filtros por fecha/actividad.
6. Consultar total de horas.

## Buenas prácticas Flask recomendadas

- Mantener patrón Application Factory.
- Separar rutas, servicios y acceso a datos.
- Usar validación de formularios (idealmente Flask-WTF + CSRF).
- Evitar lógica SQL en rutas.
- Usar migraciones (Flask-Migrate/Alembic) cuando crezca el proyecto.
- Añadir pruebas automáticas con `pytest`.
- Configurar logging y manejo de errores por entorno.

## Posibles mejoras

- Autenticación de usuarios.
- Exportación de reportes a CSV/Excel.
- Dashboard con gráficos.
- Paginación y ordenamiento en historial.
- API REST para integración con otros sistemas.

## Licencia

Uso interno/educativo. Ajustar según necesidades del proyecto.
