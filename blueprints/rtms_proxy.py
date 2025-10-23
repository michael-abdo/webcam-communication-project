"""Proxy routes for Zoom RTMS dashboard hosted on zoom-test-rtms."""

from __future__ import annotations

import os
from typing import Iterable

import requests
from flask import Blueprint, current_app, request, Response, redirect

rtms_proxy = Blueprint("rtms_proxy", __name__)

RTMS_PROXY_BASE_URL = os.getenv("RTMS_PROXY_BASE_URL", "https://zoom-test-rtms-5898b0134dc2.herokuapp.com")

# Headers that should not be forwarded from the upstream response
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _stream_response(upstream: requests.Response) -> Response:
    """Stream response from upstream to the client while copying headers."""
    headers = {
        name: value
        for name, value in upstream.headers.items()
        if name.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(upstream.iter_content(chunk_size=8192), status=upstream.status_code, headers=headers)


@rtms_proxy.route("/ws")
def proxy_websocket() -> Response:
    """Redirect websocket clients to the remote RTMS service."""
    target = f"{RTMS_PROXY_BASE_URL}/rtms/ws"
    current_app.logger.info("rtms.proxy.redirect", extra={"target": target})
    return redirect(target, code=307)


def _forward(relative_path: str) -> Response:
    target = f"{RTMS_PROXY_BASE_URL}/{relative_path}".rstrip("/")
    current_app.logger.debug(
        "rtms.proxy.forward",
        extra={"target": target, "method": request.method},
    )
    upstream = requests.request(
        method=request.method,
        url=target or RTMS_PROXY_BASE_URL,
        headers={key: value for key, value in request.headers.items() if key.lower() not in {"host", "content-length"}},
        data=request.get_data(),
        params=request.args,
        cookies=request.cookies,
        allow_redirects=False,
        stream=True,
    )
    return _stream_response(upstream)


@rtms_proxy.route("/ui", methods=["GET"])
def proxy_ui_root() -> Response:
    return _forward("")


@rtms_proxy.route("/ui/<path:path>", methods=["GET"])
def proxy_ui_asset(path: str) -> Response:
    return _forward(path)


@rtms_proxy.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@rtms_proxy.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy_http(path: str) -> Response:
    return _forward(f"rtms/{path}")
