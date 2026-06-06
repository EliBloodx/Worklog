from datetime import datetime
import io

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from modules.auth import get_user_by_id
from modules.records import (
    add_activity_option,
    add_category,
    add_state,
    get_activity_catalog,
    build_excel,
    build_records_page_context,
    build_records_page_context_for_user,
    build_reports_page_context,
    count_quick_incomplete_records,
    delete_record,
    get_record_by_id,
    get_record_filters,
    get_state_options,
    get_users_summary,
    insert_record,
    normalize_form_data,
    update_record,
)


records_bp = Blueprint("records", __name__)


@records_bp.route("/")
@login_required
def index():
    if not current_user.is_admin:
        return redirect(url_for("records.mi_inicio"))

    filters = get_record_filters(request.args)
    selected_user_id = request.args.get("user_id", "").strip()
    context = build_records_page_context(filters)
    context["admin_users"] = get_users_summary()
    context["state_options"] = get_state_options()
    context["selected_user_id"] = ""

    if selected_user_id.isdigit():
        subject_user = get_user_by_id(int(selected_user_id))
        if subject_user:
            context = build_records_page_context_for_user(
                filters,
                user_id=subject_user.id,
                subject_user=subject_user,
            )
            context["selected_user_id"] = str(subject_user.id)
            context["admin_users"] = get_users_summary()
            context["state_options"] = get_state_options()

    return render_template("index.html", **context, can_edit_all=True)


@records_bp.route("/mi-inicio")
@login_required
def mi_inicio():
    filters = get_record_filters(request.args)
    context = build_reports_page_context(
        filters,
        user_id=current_user.id,
        subject_user=current_user,
    )
    return render_template("user_home.html", **context)


@records_bp.route("/mis-registros")
@login_required
def mis_registros():
    filters = get_record_filters(request.args)
    context = build_records_page_context_for_user(
        filters,
        user_id=current_user.id,
        subject_user=current_user,
    )
    context["state_options"] = get_state_options()
    context["quick_incomplete_count"] = count_quick_incomplete_records(current_user.id)
    return render_template("index.html", **context, can_edit_all=False)


@records_bp.route("/exportar")
@login_required
def exportar():
    filters = get_record_filters(request.args)
    if current_user.is_admin:
        target_user = request.args.get("user_id", "").strip()
        if target_user.isdigit():
            context = build_records_page_context_for_user(filters, user_id=int(target_user))
        else:
            context = build_records_page_context(filters)
    else:
        context = build_records_page_context_for_user(filters, user_id=current_user.id)
    excel_bytes = build_excel(context["registros"], context["total_horas"])
    filename = f"registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        io.BytesIO(excel_bytes),
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@records_bp.route("/registro/nuevo", methods=["GET", "POST"])
@login_required
def crear_registro():
    target_user = current_user.id
    if current_user.is_admin:
        target_user_raw = request.args.get("user_id", "").strip()
        if target_user_raw.isdigit():
            candidate_user = get_user_by_id(int(target_user_raw))
            if candidate_user:
                target_user = candidate_user.id

    form_data = None
    if request.method == "POST":
        try:
            data = normalize_form_data(request.form.to_dict())
            data["user_id"] = target_user
            insert_record(data)
            flash("Registro creado correctamente", "success")
            if current_user.is_admin:
                if target_user != current_user.id:
                    return redirect(url_for("records.admin_usuario_registros", user_id=target_user))
                return redirect(url_for("records.index"))
            return redirect(url_for("records.mis_registros"))
        except ValueError as exc:
            flash(str(exc), "danger")
            form_data = request.form

    subject_user = get_user_by_id(target_user) if current_user.is_admin else current_user
    return render_template(
        "registro.html",
        registro=None,
        form_data=form_data,
        subject_user=subject_user,
        activity_catalog=get_activity_catalog(),
        state_options=get_state_options(),
    )


@records_bp.route("/registro/<int:record_id>/editar", methods=["GET", "POST"])
@login_required
def editar_registro(record_id: int):
    registro = get_record_by_id(record_id)
    if not registro:
        flash("Registro no encontrado", "warning")
        if current_user.is_admin:
            return redirect(url_for("records.index"))
        return redirect(url_for("records.mis_registros"))

    if not current_user.is_admin and registro["user_id"] != current_user.id:
        flash("No puedes editar registros de otro usuario.", "danger")
        return redirect(url_for("records.mis_registros"))

    if request.method == "POST":
        try:
            data = normalize_form_data(request.form.to_dict())
            updated = update_record(record_id, data)
            if not updated:
                flash("Registro no encontrado", "warning")
                if current_user.is_admin:
                    return redirect(url_for("records.index"))
                return redirect(url_for("records.mis_registros"))
            flash("Registro actualizado", "success")
            if current_user.is_admin:
                return redirect(url_for("records.index"))
            return redirect(url_for("records.mis_registros"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                "registro.html",
                registro=registro,
                form_data=request.form,
                subject_user=get_user_by_id(registro["user_id"]),
                activity_catalog=get_activity_catalog(),
                state_options=get_state_options(),
            )

    return render_template(
        "registro.html",
        registro=registro,
        form_data=None,
        subject_user=get_user_by_id(registro["user_id"]),
        activity_catalog=get_activity_catalog(),
        state_options=get_state_options(),
    )


@records_bp.route("/registro/rapido", methods=["POST"])
@login_required
def iniciar_registro_rapido():
    now = datetime.now()
    data = {
        "user_id": current_user.id,
        "fecha": now.strftime("%Y-%m-%d"),
        "categoria": "registro_rapido_imcompleto",
        "proyecto_equipo": "Registro rapido imcompleto",
        "cliente_referencia": "",
        "actividad": "Registro rapido imcompleto",
        "estado": "registro_rapido",
        "descripcion": "",
        "hora_inicio": now.strftime("%H:%M"),
        "hora_fin": "",
        "horas_totales": 0.0,
    }
    insert_record(data)
    flash("Registro rapido iniciado. Completa los datos al finalizar.", "info")
    return redirect(url_for("records.mis_registros"))


@records_bp.route("/registro/<int:record_id>/eliminar", methods=["POST"])
@login_required
def eliminar_registro(record_id: int):
    registro = get_record_by_id(record_id)
    if not registro:
        flash("Registro no encontrado", "warning")
        if current_user.is_admin:
            return redirect(url_for("records.index"))
        return redirect(url_for("records.mis_registros"))

    if not current_user.is_admin and registro["user_id"] != current_user.id:
        flash("No puedes eliminar registros de otro usuario.", "danger")
        return redirect(url_for("records.mis_registros"))

    deleted = delete_record(record_id)
    if deleted:
        flash("Registro eliminado", "info")
    else:
        flash("Registro no encontrado", "warning")
    if current_user.is_admin:
        return redirect(url_for("records.index"))
    return redirect(url_for("records.mis_registros"))


@records_bp.route("/admin/usuarios")
@login_required
def admin_usuarios():
    if not current_user.is_admin:
        return redirect(url_for("auth.access_denied"))

    users = get_users_summary()
    return render_template("admin_users.html", users=users, state_options=get_state_options())


@records_bp.route("/admin/usuarios/<int:user_id>/registros")
@login_required
def admin_usuario_registros(user_id: int):
    if not current_user.is_admin:
        return redirect(url_for("auth.access_denied"))

    subject_user = get_user_by_id(user_id)
    if not subject_user:
        flash("Usuario no encontrado", "warning")
        return redirect(url_for("records.admin_usuarios"))

    filters = get_record_filters(request.args)
    context = build_records_page_context_for_user(filters, user_id=user_id, subject_user=subject_user)
    context["state_options"] = get_state_options()
    return render_template("index.html", **context, can_edit_all=True)


@records_bp.route("/admin/usuarios/<int:user_id>/dashboard")
@login_required
def admin_usuario_dashboard(user_id: int):
    if not current_user.is_admin:
        return redirect(url_for("auth.access_denied"))

    subject_user = get_user_by_id(user_id)
    if not subject_user:
        flash("Usuario no encontrado", "warning")
        return redirect(url_for("records.admin_usuarios"))

    filters = get_record_filters(request.args)
    context = build_reports_page_context(filters, user_id=user_id, subject_user=subject_user)
    context["state_options"] = get_state_options()
    return render_template("reportes.html", **context)


@records_bp.route("/admin/usuarios/<int:user_id>/exportar")
@login_required
def admin_usuario_exportar(user_id: int):
    if not current_user.is_admin:
        return redirect(url_for("auth.access_denied"))

    subject_user = get_user_by_id(user_id)
    if not subject_user:
        flash("Usuario no encontrado", "warning")
        return redirect(url_for("records.admin_usuarios"))

    filters = get_record_filters(request.args)
    context = build_records_page_context_for_user(filters, user_id=user_id, subject_user=subject_user)
    excel_bytes = build_excel(context["registros"], context["total_horas"])

    period_label = "todo"
    if filters["fecha"]:
        period_label = filters["fecha"]
    elif filters["fecha_desde"] or filters["fecha_hasta"]:
        period_label = f"{filters['fecha_desde'] or 'inicio'}_{filters['fecha_hasta'] or 'hoy'}"

    filename = f"registros_{subject_user.username}_{period_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        io.BytesIO(excel_bytes),
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@records_bp.route("/admin/catalogo", methods=["GET", "POST"])
@login_required
def admin_catalogo():
    if not current_user.is_admin:
        return redirect(url_for("auth.access_denied"))

    if request.method == "POST":
        action = request.form.get("action", "").strip()

        if action == "add_category":
            ok, message = add_category(request.form.get("category_label", ""))
        elif action == "add_activity":
            ok, message = add_activity_option(
                request.form.get("category_key", ""),
                request.form.get("activity_name", ""),
            )
        elif action == "add_state":
            ok, message = add_state(request.form.get("state_label", ""))
        else:
            ok, message = False, "Accion no valida"

        flash(message, "success" if ok else "danger")
        return redirect(url_for("records.admin_catalogo"))

    return render_template(
        "admin_catalog.html",
        activity_catalog=get_activity_catalog(),
        state_options=get_state_options(),
    )
