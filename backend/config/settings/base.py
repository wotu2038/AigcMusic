"""
Django settings for AigcMusic project.
基础配置
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# 强制从 .env 读取，未提供将报错
SECRET_KEY = config('DJANGO_SECRET_KEY')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方应用
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    
    # 本地应用
    'apps.users',
    'apps.songs',
    'apps.comments',
    'apps.aigc',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'connect_timeout': 5,  # 连接超时5秒
            'read_timeout': 5,      # 读取超时5秒
            'write_timeout': 5,     # 写入超时5秒
        },
        'CONN_MAX_AGE': 300,  # 连接池保持时间（秒）- 减少到5分钟
        'AUTOCOMMIT': True,
    }
}

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型
AUTH_USER_MODEL = 'users.User'

# 登录相关配置
# 登录相关配置（SPA架构，这些配置主要用于Django Admin）
LOGIN_URL = '/admin/login/'          # Django Admin登录页
LOGIN_REDIRECT_URL = '/admin/'       # Django Admin登录后跳转

# REST Framework配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # Session认证已移除（SPA架构，统一使用JWT）
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

# JWT配置
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'user_id',  # 使用自定义主键字段
    'USER_ID_CLAIM': 'user_id',  # Token中存储用户ID的字段名
}

# CORS配置
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# Redis配置
REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT', cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD')
REDIS_DB = config('REDIS_DB', cast=int)

# Celery配置
CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_RESULT_BACKEND = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# 阿里云OSS配置
OSS_ACCESS_KEY_ID = config('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = config('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = config('OSS_ENDPOINT')
OSS_BUCKET_NAME = config('OSS_BUCKET_NAME')

# 阿里万相（通义万相）配置
ALIBABA_WANXIANG_API_KEY = config('ALIBABA_WANXIANG_API_KEY')
ALIBABA_WANXIANG_API_SECRET = config('ALIBABA_WANXIANG_API_SECRET')
ALIBABA_WANXIANG_ENDPOINT = config('ALIBABA_WANXIANG_ENDPOINT')
ALIBABA_WANXIANG_MODEL_IMAGE = config('ALIBABA_WANXIANG_MODEL_IMAGE')
ALIBABA_WANXIANG_MODEL_TEXT = config('ALIBABA_WANXIANG_MODEL_TEXT')
ALIBABA_WANXIANG_MODEL_VIDEO = config('ALIBABA_WANXIANG_MODEL_VIDEO')

