"""
生产环境配置
"""
from .base import *

DEBUG = config('DJANGO_DEBUG', cast=bool)

ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# CSRF信任的来源（通过nginx代理时需要配置）
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',')] if v else []
)

# 安全设置（HTTP环境）
# 注意：如果使用HTTP，需要将以下设置为False
# 如果后续配置HTTPS，请将这些设置改为True
SECURE_SSL_REDIRECT = False  # HTTP时不强制HTTPS重定向
SESSION_COOKIE_SECURE = False  # HTTP时设为False，HTTPS时设为True
CSRF_COOKIE_SECURE = False  # HTTP时设为False，HTTPS时设为True
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

