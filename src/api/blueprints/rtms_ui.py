"""Native RTMS dashboard blueprint."""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, current_app, jsonify, redirect, render_template, url_for


rtms_ui = Blueprint("rtms_ui", __name__)


@rtms_ui.route("/", methods=["GET"])
def rtms_root():
    """Redirect /rtms to the dashboard UI."""
    current_app.logger.info("rtms.ui.redirect", extra={"target": "/rtms/ui"})
    return redirect(url_for("rtms_ui.rtms_dashboard"), code=302)


@rtms_ui.route("/ui", methods=["GET"])
def rtms_dashboard():
    """Render the native RTMS dashboard with analytics."""
    return render_template("rtms/dashboard_analytics.html")


@rtms_ui.route("/healthz", methods=["GET"])
def rtms_health():
    """Expose hub diagnostics for fail-fast monitoring."""
    hub = current_app.config.get("RTMS_HUB")
    if hub is None:
        current_app.logger.error("rtms.ui.healthz.missing_hub")
        return jsonify({"status": "error", "details": "RTMS hub not initialised"}), 503

    return (
        jsonify(
            {
                "status": "ok",
                "connections": hub.connection_count(),
                "connected_clients": hub.connected_clients_metadata(),
            }
        ),
        200,
    )
