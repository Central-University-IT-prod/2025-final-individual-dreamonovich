import os
from os import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-p$k-g)-)8@%a$2!%p0jk-l(%yu8t8!as_mekdrlf%ac9di$vyl"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "minio_storage",
    "client",
    "business",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.middleware.LocalCacheInitializationMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ.get("POSTGRES_DATABASE", "advertising"),
        "USER": environ.get("POSTGRES_USERNAME", "postgres"),
        "PASSWORD": environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": environ.get("POSTGRES_HOST", "localhost"),
        "PORT": environ.get("POSTGRES_PORT", "5435"),
        "CONN_MAX_AGE": None,
    }
}

REDIS_HOST = environ.get("REDIS_HOST", "localhost")
REDIS_PORT = environ.get("REDIS_PORT", 6380)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}",
    },
    "local": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-local-cache",
    },
}

STORAGES = {
    "default": {
        "BACKEND": "minio_storage.storage.MinioMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "minio_storage.storage.MinioStaticStorage",
    },
    "wordlist": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": "/wordlist",
            "base_url": "/wordlist/",
        },
    },
}

STATIC_URL = "/static/"
STATIC_ROOT = "./static_files/"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ]
}

MINIO_STORAGE_ENDPOINT = os.environ.get("MINIO_S3_ENDPOINT", "localhost:9011")
MINIO_STORAGE_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "ads_service")
MINIO_STORAGE_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "ads_service_pass")
MINIO_STORAGE_USE_HTTPS = False
MINIO_STORAGE_MEDIA_BUCKET_NAME = "local-media"
MINIO_STORAGE_MEDIA_BACKUP_BUCKET = "Recycle Bin"
MINIO_STORAGE_MEDIA_BACKUP_FORMAT = "%c/"
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
# MINIO_STORAGE_MEDIA_USE_PRESIGNED = True
MINIO_STORAGE_STATIC_BUCKET_NAME = "local-static"
MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True

STORAGE_URL = os.environ.get("MINIO_STORAGE_URL", "http://localhost:9011")
MINIO_STORAGE_MEDIA_URL = f"{STORAGE_URL}/local-media"
MINIO_STORAGE_STATIC_URL = f"{STORAGE_URL}/local-static"

WSGI_APPLICATION = "app.wsgi.application"

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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

BANLIST_PATH = os.path.join(BASE_DIR, "banlist.txt")
APPEND_SLASH = True

GRAFANA_API_URL = os.environ.get("GRAFANA_API_URL", "http://localhost:3000")
GRAFANA_API_KEY = os.environ.get(
    "GRAFANA_API_KEY", "REDACTED"
)
GRAFANA_ADVERTISER_DEFAULT_PASSWORD = os.environ.get(
    "GRAFANA_ADVERTISER_DEFAULT_PASSWORD", "password"
)
GRAFANA_TEAM_ID = os.environ.get("GRAFANA_TEAM_ID", "dedbuu38t0zcwe")
