from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from modules.auth import admin_required, authenticate_user, register_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/registro-usuario", methods=["GET", "POST"])
def registro_usuario():
    if current_user.is_authenticated:
        if not current_user.is_admin:
            return redirect(url_for("records.mi_inicio"))
        return redirect(url_for("records.index"))

    form_data = {"username": "", "full_name": "", "email": ""}
    if request.method == "POST":
        username = request.form.get("username", "")
        full_name = request.form.get("full_name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        try:
            register_user(
                username=username,
                password=password,
                full_name=full_name,
                email=email,
            )
            flash("Cuenta creada correctamente. Ahora puedes iniciar sesion.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "danger")
            form_data = {
                "username": username,
                "full_name": full_name,
                "email": email,
            }

    return render_template("register.html", form_data=form_data)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if not current_user.is_admin:
            return redirect(url_for("records.mi_inicio"))
        return redirect(url_for("records.index"))

    next_url = request.args.get("next", "")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            flash("Inicio de sesion exitoso", "success")
            if not user.is_admin:
                return redirect(url_for("records.mi_inicio"))
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("records.index"))

        flash("Credenciales invalidas", "danger")

    return render_template("login.html", next_url=next_url)


@auth_bp.route("/acceso-denegado")
@login_required
def access_denied():
    return render_template("access_denied.html"), 403


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Sesion cerrada", "info")
    return redirect(url_for("auth.login"))
