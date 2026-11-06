import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
ROOT_URLCONF = "demo.urls"
WSGI_APPLICATION = "demo.wsgi.application"
INSTALLED_APPS = ["django.contrib.staticfiles"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware"]
STATIC_URL = "/static/"
STATIC_ROOT = "collected-static"
USE_TZ = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# No SQLite fallback. This HTTP contract sample doesn't use ORM or migrations.
# Customer ORM deployments must supply their existing PostgreSQL settings/driver.
DATABASES = {}
CSRF_TRUSTED_ORIGINS = [v for v in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if v]
