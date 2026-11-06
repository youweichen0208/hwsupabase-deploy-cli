import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt


def health(request):
    response = JsonResponse({"ok": True})
    response["X-HWSupabase-Release"] = os.environ.get("HWSUPABASE_RELEASE", "unversioned")
    return response


def me(request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return JsonResponse({"error": "unauthorized"}, status=401)
    req = Request(os.environ["SUPABASE_INTERNAL_URL"].rstrip("/") + "/auth/v1/user",
                  headers={"apikey": os.environ["SUPABASE_PUBLIC_KEY"], "Authorization": authorization})
    try:
        with urlopen(req, timeout=5) as result:
            user = json.load(result)
        return JsonResponse({"id": user["id"]})
    except HTTPError as error:
        return JsonResponse({"error": "unauthorized"}, status=401 if error.code in (401, 403) else 503)
    except (URLError, TimeoutError, ValueError, KeyError):
        return JsonResponse({"error": "auth-unavailable"}, status=503)


@csrf_exempt  # Disposable echo probe only; business/session views retain CSRF protection.
def contract(request, name):
    if os.environ.get("CONTRACT_TESTS") != "1":
        return HttpResponse(status=404)
    if name == "redirect":
        return HttpResponseRedirect("/healthz")
    if name == "cookies":
        response = HttpResponse("cookies", content_type="text/plain")
        response.set_cookie("first", "1", secure=True, httponly=True, samesite="Lax")
        response.set_cookie("second", "2", secure=True, httponly=True, samesite="Lax")
        return response
    if name == "binary":
        return HttpResponse(bytes(range(256)), content_type="application/octet-stream")
    if name == "error":
        return HttpResponse("expected-error", status=422, content_type="text/plain")
    return HttpResponse(request.body, content_type="application/octet-stream")


urlpatterns = [path("healthz", health), path("me", me), path("contract/<path:name>", contract)]
