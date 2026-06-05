from datetime import datetime
import io

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from modules.auth import admin_required
from modules.records import (
    build_excel,
    build_records_page_context,
    delete_record,
    get_record_by_id,
    get_record_filters,
    insert_record,
    normalize_form_data,
    update_record,
)


records_bp = Blueprint("records", __name__)


@records_bp.route("/")
@admin_required
def index():
    filters = get_record_filters(request.args)
    return render_template("index.html", **build_records_page_context(filters))


@records_bp.route("/exportar")
@admin_required
def exportar():
    filters = get_record_filters(request.args)
    context = build_records_page_context(filters)
    excel_bytes = build_excel(context["registros"], context["total_horas"])
    filename = f"registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        io.BytesIO(excel_bytes),
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@records_bp.route("/registro/nuevo", methods=["GET", "POST"])
@admin_required
def crear_registro():
    form_data = None
    if request.method == "POST":
        try:
            data = normalize_form_data(request.form.to_dict())
            insert_record(data)
            flash("Registro creado correctamente", "success")
            return redirect(url_for("records.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
            form_data = request.form

    return render_template("registro.html", registro=None, form_data=form_data)


@records_bp.route("/registro/<int:record_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_registro(record_id: int):
    registro = get_record_by_id(record_id)
    if not registro:
        flash("Registro no encontrado", "warning")
        return redirect(url_for("records.index"))

    if request.method == "POST":
        try:
            data = normalize_form_data(request.form.to_dict())
            updated = update_record(record_id, data)
            if not updated:
                flash("Registro no encontrado", "warning")
                return redirect(url_for("records.index"))
            flash("Registro actualizado", "success")
            return redirect(url_for("records.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("registro.html", registro=registro, form_data=request.form)

    return render_template("registro.html", registro=registro, form_data=None)


@records_bp.route("/registro/<int:record_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_registro(record_id: int):
    deleted = delete_record(record_id)
    if deleted:
        flash("Registro eliminado", "info")
    else:
        flash("Registro no encontrado", "warning")
    return redirect(url_for("records.index"))
