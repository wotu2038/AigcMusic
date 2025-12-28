"""
用户相关URL配置
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

# API路由（仅用于 /api/ 前缀）
api_urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', views.profile, name='profile'),
    path('users/profile/update/', views.update_profile, name='update_profile'),
    path('users/change-password/', views.change_password, name='change_password_api'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/', views.UserDetailView.as_view(), name='user_detail'),
]

# Web路由已移除（SPA架构，不再需要Web视图）
web_urlpatterns = []

# 默认导出API路由
urlpatterns = api_urlpatterns

