"""
Celery配置
"""
import os
from celery import Celery

# 设置Django默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 创建Celery应用实例
app = Celery('aigcmusic')

# 从Django设置中加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务（从所有已安装的Django应用中）
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

