from flask_login import LoginManager

from modules.auth.service import get_user_by_id


def init_login_manager(app) -> LoginManager:
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesion para acceder."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        if not user_id.isdigit():
            return None
        return get_user_by_id(int(user_id))

    return login_manager
