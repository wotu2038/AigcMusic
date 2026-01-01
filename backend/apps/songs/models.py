"""
歌曲模型
"""
from django.db import models
from django.utils import timezone
from apps.users.models import User
from utils.storage.oss_storage import audio_storage, image_storage, file_storage


# 音乐类型选择
GENRE_CHOICES = [
    ('pop', '流行'),
    ('rock', '摇滚'),
    ('jazz', '爵士'),
    ('classical', '古典'),
    ('electronic', '电子'),
    ('hiphop', '嘻哈'),
    ('r&b', 'R&B'),
    ('country', '乡村'),
    ('folk', '民谣'),
    ('blues', '蓝调'),
    ('metal', '金属'),
    ('reggae', '雷鬼'),
    ('latin', '拉丁'),
    ('world', '世界音乐'),
    ('other', '其他'),
]


class Song(models.Model):
    """歌曲模型"""
    song_id = models.AutoField(primary_key=True, verbose_name='歌曲ID')
    title = models.CharField(max_length=200, verbose_name='歌曲标题', db_index=True)
    artist = models.CharField(max_length=100, verbose_name='艺术家', db_index=True)
    album = models.CharField(max_length=100, blank=True, null=True, verbose_name='专辑', db_index=True)
    duration = models.IntegerField(verbose_name='时长(秒)')
    audio_file = models.FileField(upload_to='songs/', storage=audio_storage, blank=True, null=True, verbose_name='音频文件', help_text='支持MP3格式')
    cover_image = models.ImageField(upload_to='covers/', storage=image_storage, blank=True, null=True, verbose_name='封面图片')
    lyrics = models.TextField(blank=True, null=True, verbose_name='歌词')
    lyrics_file = models.FileField(
        upload_to='lyrics/', 
        storage=file_storage, 
        blank=True, 
        null=True, 
        verbose_name='歌词文件',
        help_text='支持LRC或SRT格式文件，上传后会自动解析并填充到歌词字段'
    )
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, blank=True, null=True, verbose_name='音乐类型', db_index=True)
    play_count = models.IntegerField(default=0, verbose_name='播放次数', db_index=True)
    like_count = models.IntegerField(default=0, verbose_name='点赞数', db_index=True)
    bitrate = models.IntegerField(blank=True, null=True, verbose_name='比特率')
    sample_rate = models.IntegerField(blank=True, null=True, verbose_name='采样率')
    is_active = models.BooleanField(default=True, verbose_name='是否激活', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'songs'
        verbose_name = '歌曲'
        verbose_name_plural = '歌曲'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title} - {self.artist}'
    
    def format_duration(self):
        """格式化时长显示"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f'{minutes}:{seconds:02d}'
    
    @property
    def file_url(self):
        """获取音频文件URL（兼容旧代码）"""
        if self.audio_file and self.audio_file.name:
            try:
                # 强制初始化bucket以确保endpoint正确
                _ = self.audio_file.storage.bucket
                return self.audio_file.url
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'获取文件URL失败: {self.audio_file.name}, 错误: {str(e)}')
                return ''
        return ''
    
    @property
    def cover_url(self):
        """获取封面图片URL（兼容旧代码）"""
        if self.cover_image and self.cover_image.name:
            try:
                # 强制初始化bucket以确保endpoint正确
                _ = self.cover_image.storage.bucket
                return self.cover_image.url
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'获取封面URL失败: {self.cover_image.name}, 错误: {str(e)}')
                return None
        return None
    
    @property
    def file_size(self):
        """获取文件大小（字节）"""
        if self.audio_file:
            try:
                return self.audio_file.size
            except:
                return None
        return None


class PlayHistory(models.Model):
    """播放历史模型"""
    history_id = models.AutoField(primary_key=True, verbose_name='历史ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', db_index=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌曲', db_index=True)
    play_duration = models.IntegerField(blank=True, null=True, verbose_name='播放时长(秒)')
    play_position = models.IntegerField(blank=True, null=True, verbose_name='播放位置(秒)')
    device_info = models.CharField(max_length=200, blank=True, null=True, verbose_name='设备信息')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='播放时间', db_index=True)
    
    class Meta:
        db_table = 'play_history'
        verbose_name = '播放历史'
        verbose_name_plural = '播放历史'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.phone} - {self.song.title}'


class SearchHistory(models.Model):
    """搜索历史模型"""
    history_id = models.AutoField(primary_key=True, verbose_name='历史ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', db_index=True)
    keyword = models.CharField(max_length=100, verbose_name='搜索关键词', db_index=True)
    search_type = models.CharField(max_length=20, blank=True, null=True, verbose_name='搜索类型')
    result_count = models.IntegerField(blank=True, null=True, verbose_name='结果数量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='搜索时间', db_index=True)
    
    class Meta:
        db_table = 'search_history'
        verbose_name = '搜索历史'
        verbose_name_plural = '搜索历史'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.phone} - {self.keyword}'
