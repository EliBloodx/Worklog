from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from modules.auth import get_user_by_id
from modules.records import (
    build_reports_page_context,
    get_record_filters,
    get_state_options,
    get_users_summary,
)


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reportes")
@login_required
def reportes():
    filters = get_record_filters(request.args)
    if current_user.is_admin:
        selected_user_id = request.args.get("user_id", "").strip()
        context = build_reports_page_context(filters)
        context["admin_users"] = get_users_summary()
        context["selected_user_id"] = ""

        if selected_user_id.isdigit():
            subject_user = get_user_by_id(int(selected_user_id))
            if subject_user:
                context = build_reports_page_context(
                    filters,
                    user_id=subject_user.id,
                    subject_user=subject_user,
                )
                context["admin_users"] = get_users_summary()
                context["selected_user_id"] = str(subject_user.id)
    else:
        context = build_reports_page_context(filters, user_id=current_user.id, subject_user=current_user)
        context["admin_users"] = []
        context["selected_user_id"] = ""
    context["state_options"] = get_state_options()
    return render_template("reportes.html", **context)
