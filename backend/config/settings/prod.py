from .base import *

DEBUG = False

# 필수 환경변수 검증
_REQUIRED_ENV = ['DJANGO_SECRET_KEY', 'DB_PASSWORD', 'ALLOWED_HOSTS']
_missing = [k for k in _REQUIRED_ENV if not os.environ.get(k)]
if _missing:
    raise ValueError(f"Missing required environment variables: {', '.join(_missing)}")

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'blog_jun'),
        'USER': os.environ.get('DB_USER', 'blog_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    },
    'throttle': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0').rsplit('/', 1)[0] + '/1',
    },
}

# Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Cloudflare handles SSL
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# DRF Throttling (Redis-backed - 워커 간 공유)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [
        'blog.throttles.RedisAnonRateThrottle',
        'blog.throttles.RedisUserRateThrottle',
    ],
    # 공개 블로그는 한 페이지를 그리는 데 API를 여러 번 부른다(피드·카테고리·시리즈·
    # 포스트링크·통계). 익명 100/hour면 방문자가 열 몇 페이지만 봐도 한도가 차서
    # 목록이 통째로 빈 화면이 됐다. 읽기는 캐시가 받쳐주므로 넉넉히 연다.
    'DEFAULT_THROTTLE_RATES': {
        'anon': '3000/hour',
        'user': '10000/hour',
        'comment': '10/hour',
    },
}

# Logging
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
