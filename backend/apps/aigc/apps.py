"""
AIGC应用配置
"""
from django.apps import AppConfig


class AigcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.aigc'
    verbose_name = 'AIGC内容生成'

