"""
URL configuration for AigcMusic project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def health_check(request):
    """健康检查端点"""
    return JsonResponse({"status": "healthy", "timestamp": "2025-12-28"})
from apps.songs.urls import api_urlpatterns
from apps.users.urls import api_urlpatterns as users_api_urlpatterns
from apps.comments.urls import urlpatterns as comments_urlpatterns
from apps.aigc.urls import urlpatterns as aigc_urlpatterns

# 合并所有API路由到一个列表，使用统一的namespace
# Web路由已移除（SPA架构，不再需要Web视图）
all_api_urlpatterns = users_api_urlpatterns + api_urlpatterns + comments_urlpatterns + aigc_urlpatterns

schema_view = get_schema_view(
   openapi.Info(
      title="AigcMusic API",
      default_version='v1',
      description="AigcMusic音乐应用API文档",
      terms_of_service="https://www.aigcmusic.com/terms/",
      contact=openapi.Contact(email="contact@aigcmusic.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # 健康检查
    path('health/', health_check, name='health_check'),

    # API文档
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API路由 - 合并所有API路由，避免namespace冲突
    path('api/', include((all_api_urlpatterns, 'api'), namespace='api')),
    
    # Web路由已移除（SPA架构，前端由React处理）
]

# 开发环境：提供静态文件和媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

