from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "mini_service.urls"
WSGI_APPLICATION = "mini_service.wsgi.application"


def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


# Switch DB backend automatically:
# - If POSTGRES_RESERVATIONS_HOST is set, use Postgres (cluster)
# - Otherwise, use SQLite (local dev)
if env("POSTGRES_RESERVATIONS_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_RESERVATIONS_DBNAME", "reservations_v3"),
            "USER": env("POSTGRES_RESERVATIONS_USER", "postgres"),
            "PASSWORD": env("POSTGRES_RESERVATIONS_PASSWORD", "postgres"),
            "HOST": env("POSTGRES_RESERVATIONS_HOST", "postgres"),
            "PORT": env("POSTGRES_RESERVATIONS_PORT", "5432"),
            # Optional but nice: avoids stale connections
            "CONN_MAX_AGE": int(env("POSTGRES_CONN_MAX_AGE", "60") or "60"),
        }
    }
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"