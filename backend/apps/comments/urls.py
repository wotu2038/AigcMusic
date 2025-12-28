"""
评论相关URL配置
"""
from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # API路由（注意：主URL配置已经包含api/前缀，这里不需要再加）
    path('songs/<int:song_id>/comments/', views.comment_list, name='comment_list_api'),
    path('songs/<int:song_id>/comments/create/', views.comment_create, name='comment_create_api'),
    path('comments/<int:comment_id>/like/', views.comment_like, name='comment_like_api'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete_api'),
]

