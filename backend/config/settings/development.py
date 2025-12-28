"""
开发环境配置
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

# CSRF Cookie设置（通过nginx代理时）
CSRF_COOKIE_SECURE = False  # HTTP时设为False，HTTPS时设为True
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False

# 开发环境允许所有CORS
CORS_ALLOW_ALL_ORIGINS = True

# 开发工具
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1', 'localhost', '0.0.0.0']
    except ImportError:
        pass

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

