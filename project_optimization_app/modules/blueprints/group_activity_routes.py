from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from modules.group_activities import (
    build_admin_group_activities_context,
    close_activity,
    create_group_activity,
    join_group_activity,
)


group_activities_bp = Blueprint("group_activities", __name__)


@group_activities_bp.route("/actividades-grupales/<int:activity_id>/unirse", methods=["POST"])
@login_required
def unirse_actividad_grupal(activity_id: int):
    ok, message = join_group_activity(activity_id, current_user.id)
    flash(message, "success" if ok else "danger")
    return redirect(url_for("records.mis_registros") if ok else url_for("records.mi_inicio"))


@group_activities_bp.route("/admin/actividades-grupales", methods=["GET", "POST"])
@login_required
def admin_actividades_grupales():
    if not current_user.is_admin:
        return redirect(url_for("auth.access_denied"))

    if request.method == "POST":
        action = request.form.get("action", "").strip()
        if action == "create_group_activity":
            ok, message = create_group_activity(request.form.to_dict(), current_user.id)
        elif action == "close_group_activity":
            activity_id_raw = request.form.get("group_activity_id", "").strip()
            if activity_id_raw.isdigit():
                ok, message = close_activity(int(activity_id_raw))
            else:
                ok, message = False, "La actividad grupal no es valida"
        else:
            ok, message = False, "Accion no valida"

        flash(message, "success" if ok else "danger")
        return redirect(url_for("group_activities.admin_actividades_grupales"))

    context = build_admin_group_activities_context()
    return render_template("admin_group_activities.html", **context)