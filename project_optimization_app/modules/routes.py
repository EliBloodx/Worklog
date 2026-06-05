from flask import Flask

from modules.blueprints import register_blueprints as register_project_blueprints


def register_blueprints_for_app(app: Flask) -> None:
    register_project_blueprints(app)


register_blueprints = register_blueprints_for_app
