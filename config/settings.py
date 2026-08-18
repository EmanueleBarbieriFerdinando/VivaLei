from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-wi(h(up60%)6$*17vw!%vm(bemp=fb1f%%e$g@)bzjk*_m4*5u"
)

DEBUG = True

ALLOWED_HOSTS = []


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


INSTALLED_APPS = [
    "carrello",
    "core",
    "users",
    "products",
    "gestione",
    "orders",
    "support",
    "tinymce",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "carrello.context_processors.dati_carrello",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "it-it"

TIME_ZONE = "Europe/Rome"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


AUTH_USER_MODEL = "users.User"

LOGIN_URL = "users:login"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "users:login"

# EMAIL CONFIGURATION

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"

EMAIL_PORT = 587

EMAIL_USE_TLS = True


EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    ""
)


EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    ""
)


DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# EMAIL IMAP CONFIGURATION

EMAIL_IMAP_HOST = "imap.gmail.com"

EMAIL_IMAP_PORT = 993


EMAIL_IMAP_USER = os.getenv(
    "EMAIL_HOST_USER",
    ""
)


EMAIL_IMAP_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    ""
)