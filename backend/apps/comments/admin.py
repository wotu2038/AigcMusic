"""
评论管理后台
"""
from django.contrib import admin
from .models import Comment, UserCommentLike


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """评论管理"""
    list_display = ('comment_id', 'user', 'song', 'content_preview', 'like_count', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__phone', 'song__title', 'content')
    readonly_fields = ('comment_id', 'like_count', 'created_at', 'updated_at')
    
    def content_preview(self, obj):
        """内容预览"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '内容预览'


@admin.register(UserCommentLike)
class UserCommentLikeAdmin(admin.ModelAdmin):
    """用户评论点赞管理"""
    list_display = ('like_id', 'user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__phone', 'comment__content')
    readonly_fields = ('like_id', 'created_at')
