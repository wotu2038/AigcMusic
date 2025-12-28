"""
用户管理后台
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    list_display = ('phone', 'nickname', 'is_vip', 'coin_balance', 'is_active', 'date_joined')
    list_filter = ('is_vip', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('phone', 'nickname')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('个人信息', {'fields': ('nickname', 'avatar_url')}),
        ('VIP信息', {'fields': ('is_vip', 'vip_type', 'vip_expire_at')}),
        ('金币', {'fields': ('coin_balance',)}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2'),
        }),
    )

