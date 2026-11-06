"""Disposable HTTP contract sample. CONTRACT_TESTS is off for production."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, redirect, request

app = Flask(__name__)


@app.get("/healthz")
def health():
    response = jsonify(ok=True)
    response.headers["X-HWSupabase-Release"] = os.environ.get("HWSUPABASE_RELEASE", "unversioned")
    return response


@app.get("/me")
def me():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return jsonify(error="unauthorized"), 401
    # Auth validates the user token. Never trust a decoded-but-unverified JWT.
    endpoint = os.environ["SUPABASE_INTERNAL_URL"].rstrip("/") + "/auth/v1/user"
    req = Request(endpoint, headers={"apikey": os.environ["SUPABASE_PUBLIC_KEY"], "Authorization": authorization})
    try:
        with urlopen(req, timeout=5) as result:
            user = json.load(result)
        return jsonify(id=user["id"])
    except HTTPError as error:
        return jsonify(error="unauthorized" if error.code in (401, 403) else "auth-unavailable"), 401 if error.code in (401, 403) else 503
    except (URLError, TimeoutError, ValueError, KeyError):
        return jsonify(error="auth-unavailable"), 503


@app.route("/contract/<path:name>", methods=["GET", "POST", "OPTIONS"])
def contract(name):
    if os.environ.get("CONTRACT_TESTS") != "1":
        return jsonify(error="not-found"), 404
    if name == "redirect":
        return redirect("/healthz", code=302)
    if name == "cookies":
        response = Response("cookies", content_type="text/plain")
        response.set_cookie("first", "1", secure=True, httponly=True, samesite="Lax")
        response.set_cookie("second", "2", secure=True, httponly=True, samesite="Lax")
        return response
    if name == "binary":
        return Response(bytes(range(256)), content_type="application/octet-stream")
    if name == "error":
        return Response("expected-error", status=422, content_type="text/plain")
    return Response(request.get_data(), status=200, content_type="application/octet-stream")
