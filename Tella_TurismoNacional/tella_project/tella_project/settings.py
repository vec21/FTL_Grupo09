from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de ambiente de um arquivo .env se existir
def _load_env_files():
    try:
        # Usa python-dotenv se disponível
        from dotenv import load_dotenv  # type: ignore
        for p in [BASE_DIR / '.env', BASE_DIR.parent / '.env']:
            if p.exists():
                load_dotenv(p)
    except Exception:
        # Fallback simples: parsing manual
        for p in [BASE_DIR / '.env', BASE_DIR.parent / '.env']:
            try:
                if p.exists():
                    for line in p.read_text(encoding='utf-8').splitlines():
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())
            except Exception:
                pass

_load_env_files()

# Segurança e ambiente
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-before-prod')
DEBUG = (os.getenv('DEBUG', '1').lower() in ('1', 'true', 'yes'))

# ALLOWED_HOSTS via env (separado por vírgula). Em produção (Render), incluir domínio.
_allowed = os.getenv('ALLOWED_HOSTS', '').strip()
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()] or ([] if DEBUG else ['.onrender.com'])

# Render: hostname externo para CSRF e hosts de confiança
_render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if _render_host:
    if _render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_render_host)
    CSRF_TRUSTED_ORIGINS = [f"https://{_render_host}", "https://*.onrender.com"]
else:
    CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tella_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tella_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
# Inclui a pasta static do projeto
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
# WhiteNoise para arquivos estáticos em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

# External APIs
_raw_rapidapi = os.getenv('RAPIDAPI_KEY', '')
RAPIDAPI_KEY = _raw_rapidapi.strip() or None
RAPIDAPI_HOST = 'google-map-places-new-v2.p.rapidapi.com'

# Cache (evitar bater na API a cada requisição)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'tella-cache',
    }
}
# TTL padrão (segundos) para resultados de Places
PLACES_CACHE_TTL = int(os.getenv('PLACES_CACHE_TTL', '600'))  # 10 min por default

# Segurança em produção / proxies Render
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

# Logging estruturado
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'ml': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}
