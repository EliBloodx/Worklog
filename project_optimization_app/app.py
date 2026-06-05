from flask import Flask

from config import APP_DEBUG, APP_HOST, APP_PORT, SECRET_KEY
from modules.auth import init_login_manager
from modules.database import init_db
from modules.routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    init_login_manager(app)

    init_db()
    register_blueprints(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)