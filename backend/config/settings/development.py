"""
开发环境配置
"""
from .base import *

DEBUG = config('DJANGO_DEBUG', cast=bool)

ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

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

