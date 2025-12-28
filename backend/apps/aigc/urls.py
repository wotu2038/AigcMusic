"""
AIGC相关URL配置
"""
from django.urls import path
from . import views

app_name = 'aigc'

urlpatterns = [
    # API路由（供Web和iOS使用）
    path('songs/<int:song_id>/aigc/', views.song_aigc_content, name='song_aigc_content'),
    
    # 运营后台API路由
    path('admin/tasks/', views.task_list, name='task_list'),
    path('admin/tasks/create/', views.task_create, name='task_create'),
    path('admin/tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('admin/contents/', views.content_list, name='content_list'),
    path('admin/contents/<int:content_id>/review/', views.content_review, name='content_review'),
    path('admin/contents/<int:content_id>/publish/', views.content_publish, name='content_publish'),
]

