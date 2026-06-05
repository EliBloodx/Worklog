from flask import Blueprint, render_template, request

from modules.auth import admin_required
from modules.records import build_reports_page_context, get_record_filters


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reportes")
@admin_required
def reportes():
    filters = get_record_filters(request.args)
    return render_template("reportes.html", **build_reports_page_context(filters))
