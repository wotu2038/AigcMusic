"""
歌曲管理后台
"""
import logging
from django.contrib import admin
from django.contrib import messages
from .models import Song, PlayHistory, SearchHistory

logger = logging.getLogger(__name__)


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    """歌曲管理"""
    list_display = ('song_id', 'title', 'artist', 'album', 'duration', 'genre', 'play_count', 'like_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'genre', 'created_at')
    search_fields = ('title', 'artist', 'album')
    readonly_fields = ('song_id', 'play_count', 'like_count', 'file_size', 'created_at', 'updated_at', 'file_url', 'cover_url')
    fieldsets = (
        ('基本信息', {
            'fields': ('song_id', 'title', 'artist', 'album', 'duration', 'genre')
        }),
        ('文件信息', {
            'fields': ('audio_file', 'cover_image', 'file_size', 'bitrate', 'sample_rate', 'file_url', 'cover_url'),
            'description': '音频文件支持MP3格式，将自动上传到阿里云OSS'
        }),
        ('其他信息', {
            'fields': ('lyrics', 'play_count', 'like_count', 'is_active', 'created_at', 'updated_at')
        }),
    )
    
    def file_size(self, obj):
        """显示文件大小"""
        if obj.audio_file:
            try:
                size = obj.audio_file.size
                if size:
                    # 转换为MB
                    return f'{size / (1024 * 1024):.2f} MB'
            except:
                pass
        return '-'
    file_size.short_description = '文件大小'
    
    def save_model(self, request, obj, form, change):
        """保存模型时记录日志"""
        try:
            logger.info(f'保存歌曲: {obj.title}, 音频文件: {obj.audio_file.name if obj.audio_file else None}, 封面: {obj.cover_image.name if obj.cover_image else None}')
            super().save_model(request, obj, form, change)
            if obj.audio_file:
                logger.info(f'音频文件URL: {obj.file_url}')
            if obj.cover_image:
                logger.info(f'封面URL: {obj.cover_url}')
        except Exception as e:
            logger.error(f'保存歌曲失败: {str(e)}', exc_info=True)
            messages.error(request, f'保存失败: {str(e)}')
            raise


@admin.register(PlayHistory)
class PlayHistoryAdmin(admin.ModelAdmin):
    """播放历史管理"""
    list_display = ('history_id', 'user', 'song', 'play_duration', 'play_position', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__phone', 'song__title')
    readonly_fields = ('history_id', 'created_at')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """搜索历史管理"""
    list_display = ('history_id', 'user', 'keyword', 'search_type', 'result_count', 'created_at')
    list_filter = ('search_type', 'created_at')
    search_fields = ('user__phone', 'keyword')
    readonly_fields = ('history_id', 'created_at')
