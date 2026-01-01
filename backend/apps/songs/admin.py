"""
歌曲管理后台
"""
import logging
from django.contrib import admin
from django.contrib import messages
from .models import Song, PlayHistory, SearchHistory
from .utils.lyrics_parser import parse_lyrics_file

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
            'fields': ('audio_file', 'cover_image', 'mv_video_file', 'file_size', 'bitrate', 'sample_rate', 'file_url', 'cover_url'),
            'description': '音频文件支持MP3格式，MV视频文件支持MP4格式（建议720p或1080p，不超过500MB），将自动上传到阿里云OSS'
        }),
        ('歌词信息', {
            'fields': ('lyrics_file', 'lyrics'),
            'description': '支持上传LRC或SRT格式文件，上传后会自动解析并填充到歌词字段。也可以直接编辑歌词文本。'
        }),
        ('其他信息', {
            'fields': ('play_count', 'like_count', 'is_active', 'created_at', 'updated_at')
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
        """保存模型时处理歌词文件解析"""
        try:
            # 检查是否上传了新的歌词文件
            # 注意：在保存前检查，因为保存后文件指针会改变
            lyrics_file_uploaded = False
            lyrics_file_content = None
            lyrics_file_name = None
            
            if obj.lyrics_file:
                # 检查是否是新建或文件被修改
                if not change or 'lyrics_file' in form.changed_data:
                    lyrics_file_uploaded = True
                    try:
                        obj.lyrics_file.seek(0)
                        lyrics_file_content = obj.lyrics_file.read()
                        lyrics_file_name = obj.lyrics_file.name
                        obj.lyrics_file.seek(0)  # 重置文件指针
                    except Exception as e:
                        logger.error(f'读取歌词文件失败: {str(e)}')
                        lyrics_file_uploaded = False
            
            if lyrics_file_uploaded and lyrics_file_content:
                try:
                    # 解析歌词文件
                    result = parse_lyrics_file(lyrics_file_content, lyrics_file_name)
                    
                    if result['format'] in ('lrc', 'srt'):
                        # 将解析后的内容转换为文本格式存储
                        # 对于LRC格式，直接使用原始内容
                        # 对于SRT格式，转换为LRC格式存储（兼容前端）
                        if result['format'] == 'lrc':
                            # LRC格式直接使用原始内容
                            obj.lyrics = result['content']
                        else:
                            # SRT格式转换为LRC格式（使用开始时间）
                            lrc_lines = []
                            for item in result['parsed']:
                                time_sec = item['time']
                                minutes = int(time_sec // 60)
                                seconds = int(time_sec % 60)
                                centiseconds = int((time_sec % 1) * 100)
                                time_tag = f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"
                                lrc_lines.append(f"{time_tag}{item['text']}")
                            obj.lyrics = '\n'.join(lrc_lines)
                        
                        messages.success(
                            request, 
                            f'歌词文件解析成功（格式: {result["format"].upper()}），已自动填充到歌词字段'
                        )
                        logger.info(f'歌词文件解析成功: {lyrics_file_name}, 格式: {result["format"]}, 行数: {len(result["parsed"])}')
                    else:
                        # 纯文本格式
                        obj.lyrics = result['content']
                        messages.info(request, '歌词文件已上传，但未检测到时间标签，已作为纯文本保存')
                        logger.info(f'歌词文件作为纯文本保存: {lyrics_file_name}')
                except Exception as e:
                    logger.error(f'解析歌词文件失败: {str(e)}', exc_info=True)
                    messages.warning(request, f'歌词文件上传成功，但解析失败: {str(e)}。请手动编辑歌词字段。')
            
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
