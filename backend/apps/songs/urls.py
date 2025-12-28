"""
歌曲相关URL配置
"""
from django.urls import path
from . import views

app_name = 'songs'

# API路由（仅用于 /api/ 前缀）
# 注意：更具体的路由要放在前面，避免被通用路由匹配
api_urlpatterns = [
    path('songs/', views.SongListView.as_view(), name='song_list_api'),
    path('songs/<int:song_id>/stream/', views.stream_audio, name='stream_audio_api'),
    path('songs/<int:song_id>/play/', views.play_song, name='play_song_api'),
    path('songs/<int:song_id>/like/', views.like_song, name='like_song_api'),
    path('songs/<int:song_id>/', views.SongDetailView.as_view(), name='song_detail_api'),
]

# Web路由已移除（SPA架构，不再需要Web视图）
web_urlpatterns = []

# 默认导出API路由
urlpatterns = api_urlpatterns

