"""
Django settings for config project.

Security note: nothing secret lives in this file. Every value that
differs between developers or between dev/prod (SECRET_KEY, DEBUG,
DB credentials, allowed hosts, CORS origins, LLM key) is read from
environment variables via django-environ, loaded from backend/.env
(git-ignored). See backend/.env.example for the template.
"""
# Bu dosyada hiçbir gizli değer (secret) doğrudan yazılı durmuyor.
# Geliştiriciden geliştiriciye ya da ortamdan ortama (dev/prod) değişen her
# şey — SECRET_KEY, DEBUG, veritabanı bilgileri, izinli host'lar, CORS
# kaynakları, LLM anahtarı — django-environ ile backend/.env dosyasından
# okunuyor. .env dosyası git'e asla eklenmez (.gitignore'da), şablonu ise
# backend/.env.example'dadır. Böylece kod deposuna yanlışlıkla şifre/anahtar
# sızmaz ve her geliştirici kendi yerel .env'ini kullanır.

from datetime import timedelta
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# environ.Env, ortam değişkenlerini (env var) doğru tipe çevirerek
# (str -> bool, str -> list) okumamızı sağlıyor; örn. "True" string'ini
# gerçek Python bool'una çeviriyor.
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
# .env dosyası varsa oku (yerel geliştirme). Prod'da .env yerine gerçek
# ortam değişkenleri (örn. hosting sağlayıcısının secret store'u) kullanılır;
# dosya yoksa hata vermez, sadece os.environ'a düşer.
environ.Env.read_env(BASE_DIR / ".env")


# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY için varsayılan (default) DEĞERİ BİLEREK VERMİYORUZ.
# Eğer .env'de DJANGO_SECRET_KEY tanımlı değilse, django-environ hata
# fırlatıp uygulamayı başlatmaz — "unutulmuş secret key" ile production'a
# çıkmayı imkansız hale getiren bilinçli bir güvenlik tercihi.
SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG=True iken hata sayfaları kaynak kodu, ayarları ve stack trace'i
# olduğu gibi tarayıcıya döker. Bu yüzden prod'da DAİMA False olmalı;
# değeri .env üzerinden ortama göre ayarlıyoruz (dev'de True, prod'da False).
DEBUG = env("DJANGO_DEBUG")

# DEBUG=False iken Django, ALLOWED_HOSTS'ta olmayan bir Host header'ıyla
# gelen isteği reddeder (HTTP Host header saldırılarına karşı temel savunma).
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # --- Third-party ---
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    # --- Local ---
    "core",
    "users",
    "vehicles",
    "reservations",
    "handovers",
    "service_requests",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware, CommonMiddleware'den ÖNCE gelmeli (django-cors-headers
    # dokümantasyonunun şartı) — aksi halde CORS header'ları bazı yanıtlarda
    # eksik kalabilir.
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# PDF'in tech stack'i PostgreSQL 16 istiyor (SQLite değil). Bağlantı
# bilgileri (DB adı, kullanıcı, şifre, host, port) tamamen .env'den okunuyor
# — böylece backend/.env.example'daki POSTGRES_* değerlerini değiştirerek
# kod dokunmadan farklı bir veritabanına (örn. test DB'sine) bağlanabiliriz.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django'ya "varsayılan User modelini kullanma, benim yazdığım
# users.User'ı kullan" diyoruz. Bu satır, ilk migration'dan ÖNCE burada
# olmak ZORUNDA — sonradan değiştirmek yeni bir proje açmak kadar zahmetli.
AUTH_USER_MODEL = "users.User"


# ------------------------------------------------------------------
# Django REST Framework
# ------------------------------------------------------------------
# DEFAULT_AUTHENTICATION_CLASSES -> gelen her isteğin Authorization
# header'ındaki JWT'yi kim çözecek (SimpleJWT). DEFAULT_PERMISSION_CLASSES
# -> hiçbir view kendi permission_classes'ını belirtmezse ne olacak: biz
# "varsayılan olarak KİMSE giremez, izin verilmemişse reddet" (IsAuthenticated)
# tercih ettik — güvenli varsayılan (secure by default). Bir endpoint'i
# gerçekten herkese açmak istersen (örn. araç arama), onu view içinde
# AllowAny ile AÇIKÇA belirtmen gerekir; "unutulduğu için açık kaldı" riski
# böylece ortadan kalkar.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ------------------------------------------------------------------
# SimpleJWT
# ------------------------------------------------------------------
# access token kısa ömürlü (60 dk) — çalınsa bile hızla geçersiz olur.
# refresh token daha uzun (7 gün) — sadece yeni access almak için kullanılır,
# normal API isteklerinde GÖNDERİLMEZ. ROTATE_REFRESH_TOKENS + BLACKLIST,
# her refresh'te eskisini geçersiz kılıp yenisini verir (çalıntı bir refresh
# token'ın sonsuza kadar geçerli kalmasını engeller).
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ------------------------------------------------------------------
# drf-spectacular (Swagger / OpenAPI docs)
# ------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "RentAI API",
    "DESCRIPTION": "Araç kiralama ve rezervasyon platformu — staj projesi API'si.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ------------------------------------------------------------------
# CORS (which frontend origins may call this API)
# ------------------------------------------------------------------
# Tarayıcı, farklı bir origin'den (örn. localhost:5173 -> localhost:8000)
# gelen isteklere sunucunun izin verip vermediğini CORS header'larından
# anlar. CORS_ALLOW_ALL_ORIGINS=True DEMİYORUZ — sadece .env'de listelenen,
# bilinen frontend origin'lerine izin veriyoruz (varsayılan: Vite dev sunucusu).
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)

# ------------------------------------------------------------------
# Production hardening — sadece DEBUG=False iken devreye girer
# ------------------------------------------------------------------
# Bu ayarlar yerel geliştirmede (DEBUG=True, http://localhost) devrede
# OLMAMALI — yoksa http üzerinden localhost'a bile bağlanamazsın. Sadece
# gerçek bir prod ortamına (DEBUG=False, gerçek domain + HTTPS) çıkarken
# otomatik olarak aktif olurlar.
if not DEBUG:
    SECURE_SSL_REDIRECT = True          # http isteklerini https'e yönlendir
    SESSION_COOKIE_SECURE = True        # session cookie'si sadece https üzerinden gönderilsin
    CSRF_COOKIE_SECURE = True           # csrf cookie'si sadece https üzerinden gönderilsin
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # taraycıya 30 gün boyunca hep https kullan de
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
