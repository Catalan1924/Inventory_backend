# inventory_backend/settings.py
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# SECURITY / DEBUG
# -------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key")

# DEBUG should be "True" or "False" string in the environment.
DEBUG = os.environ.get("DEBUG", "False") == "True"

# -------------------------
# HOSTS (flexible)
# -------------------------
# Default hosts for local & quick deploy; you can override via ALLOWED_HOSTS env var
DEFAULT_ALLOWED = ["localhost", "127.0.0.1", "0.0.0.0"]

_env_allowed = os.environ.get("ALLOWED_HOSTS")
if _env_allowed:
    # allow comma-separated values in the env var
    ALLOWED_HOSTS = [h.strip() for h in _env_allowed.split(",") if h.strip()]
else:
    # include Render's automatic host env if available
    render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_host:
        ALLOWED_HOSTS = [render_host] + DEFAULT_ALLOWED
    else:
        # sensible default for your Render app plus locals
        ALLOWED_HOSTS = ["inventory-backend-1-kcep.onrender.com"] + DEFAULT_ALLOWED

# In DEBUG mode it's sometimes convenient to allow all hosts locally
if DEBUG:
    ALLOWED_HOSTS = ["*"]

# -------------------------
# INSTALLED APPS / MIDDLEWARE
# -------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",

    # local apps
    "inventory",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # whitenoise serves static files in many PaaS setups
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # corsheaders should be near the top
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "inventory_backend.urls"
WSGI_APPLICATION = "inventory_backend.wsgi.application"

# -------------------------
# TEMPLATES
# -------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------
# DATABASE (DATABASE_URL fallback to sqlite)
# -------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # parse DATABASE_URL (Postgres on Render / production)
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
    }
else:
    # local fallback to sqlite so `manage.py migrate` works without DB env var
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# -------------------------
# AUTH / PASSWORD VALIDATORS
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------
# I18N / TIMEZONE
# -------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# -------------------------
# STATIC FILES
# -------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------
# CORS / CSRF
# -------------------------
# Allow origins from env if provided; otherwise use the frontend origin
_env_cors = os.environ.get("CORS_ALLOWED_ORIGINS")
if _env_cors:
    CORS_ALLOWED_ORIGINS = [u.strip() for u in _env_cors.split(",") if u.strip()]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "https://inventory-frontend-henna-five.vercel.app",
    ]

# Optionally allow all origins (useful for quick debugging only)
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False") == "True"

CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins (Django requires full origin with scheme)
_csrf_env = os.environ.get("CSRF_TRUSTED_ORIGINS")
if _csrf_env:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _csrf_env.split(",") if u.strip()]
else:
    # include the frontend origin and the rendered backend if available
    render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    CSRF_TRUSTED_ORIGINS = [
        "https://inventory-frontend-henna-five.vercel.app",
    ]
    if render_host:
        CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

# -------------------------
# PROXY / HTTPS (for Render)
# -------------------------
# If behind a proxy or load balancer that sets X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -------------------------
# REST FRAMEWORK
# -------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        # "rest_framework.authentication.SessionAuthentication",  # optional
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# -------------------------
# OPTIONAL: simple logging to console for debugging deploys
# -------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
