from flask import Flask

from modules.blueprints.auth_routes import auth_bp
from modules.blueprints.records_routes import records_bp
from modules.blueprints.reports_routes import reports_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(reports_bp)
