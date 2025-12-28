"""
AIGC内容生成模型
"""
from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.songs.models import Song
from utils.storage.oss_storage import image_storage, video_storage


# 生成任务类型
TASK_TYPE_CHOICES = [
    ('lyric_image', '歌词配图'),
    ('comment_summary', '评论摘要'),
    ('lyric_video', '歌词视频'),
    ('text_to_video', '文生视频'),
]

# 任务状态
TASK_STATUS_CHOICES = [
    ('pending', '待处理'),
    ('processing', '处理中'),
    ('completed', '已完成'),
    ('failed', '失败'),
]

# 内容状态
CONTENT_STATUS_CHOICES = [
    ('pending_review', '待审核'),
    ('approved', '已通过'),
    ('rejected', '已拒绝'),
    ('published', '已发布'),
]

# 图片生成风格
IMAGE_STYLE_CHOICES = [
    ('beautiful', '唯美'),
    ('abstract', '抽象'),
    ('realistic', '写实'),
    ('minimalist', '简约'),
    ('artistic', '艺术'),
]

# 摘要风格
SUMMARY_STYLE_CHOICES = [
    ('objective', '客观评价'),
    ('subjective', '主观感受'),
    ('emotional', '情感分析'),
]


class AIGCGenerationTask(models.Model):
    """AIGC生成任务模型"""
    task_id = models.AutoField(primary_key=True, verbose_name='任务ID')
    task_type = models.CharField(
        max_length=50, 
        choices=TASK_TYPE_CHOICES, 
        verbose_name='任务类型',
        db_index=True
    )
    song = models.ForeignKey(
        Song, 
        on_delete=models.CASCADE, 
        verbose_name='歌曲',
        db_index=True
    )
    operator = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='操作人员',
        db_index=True
    )
    status = models.CharField(
        max_length=20, 
        choices=TASK_STATUS_CHOICES, 
        default='pending',
        verbose_name='任务状态',
        db_index=True
    )
    parameters = models.JSONField(
        default=dict,
        verbose_name='生成参数',
        help_text='存储生成任务的参数，如风格、数量等'
    )
    error_message = models.TextField(
        null=True, 
        blank=True,
        verbose_name='错误信息'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='创建时间',
        db_index=True
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='完成时间'
    )
    
    class Meta:
        db_table = 'aigc_generation_tasks'
        verbose_name = 'AIGC生成任务'
        verbose_name_plural = 'AIGC生成任务'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['song', 'task_type', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.get_task_type_display()} - {self.song.title} ({self.get_status_display()})'


class AIGCContent(models.Model):
    """AIGC生成内容模型"""
    content_id = models.AutoField(primary_key=True, verbose_name='内容ID')
    task = models.ForeignKey(
        AIGCGenerationTask, 
        on_delete=models.CASCADE, 
        verbose_name='生成任务',
        db_index=True
    )
    content_type = models.CharField(
        max_length=20, 
        verbose_name='内容类型',
        help_text='image: 图片, text: 文字, video: 视频'
    )
    content_url = models.URLField(
        max_length=500,
        verbose_name='内容URL',
        help_text='OSS存储URL'
    )
    content_file = models.FileField(
        upload_to='aigc/images/',
        storage=image_storage,
        null=True,
        blank=True,
        verbose_name='内容文件',
        help_text='图片或视频文件'
    )
    content_video_file = models.FileField(
        upload_to='aigc/videos/',
        storage=video_storage,
        null=True,
        blank=True,
        verbose_name='视频文件',
        help_text='视频文件（仅视频类型）'
    )
    content_text = models.TextField(
        null=True,
        blank=True,
        verbose_name='内容文本',
        help_text='文字内容（仅文字类型）'
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name='元数据',
        help_text='存储内容的元数据，如尺寸、风格、字数等'
    )
    status = models.CharField(
        max_length=20, 
        choices=CONTENT_STATUS_CHOICES, 
        default='pending_review',
        verbose_name='内容状态',
        db_index=True
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='审核时间'
    )
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_aigc_contents',
        verbose_name='审核人员'
    )
    review_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='审核备注'
    )
    published_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='发布时间',
        db_index=True
    )
    usage_count = models.IntegerField(
        default=0,
        verbose_name='使用次数',
        help_text='内容被使用的次数（前端展示次数）'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='创建时间',
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 'aigc_contents'
        verbose_name = 'AIGC生成内容'
        verbose_name_plural = 'AIGC生成内容'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'status']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['content_type', 'status']),
        ]
    
    def __str__(self):
        return f'{self.content_type} - {self.task.song.title} ({self.get_status_display()})'
    
    @property
    def display_url(self):
        """获取内容显示URL（优先使用content_file，其次使用content_url）"""
        # 视频类型优先使用content_video_file
        if self.content_type == 'video' and self.content_video_file and self.content_video_file.name:
            try:
                _ = self.content_video_file.storage.bucket
                return self.content_video_file.url
            except Exception:
                return self.content_url or ''
        
        # 图片类型使用content_file
        if self.content_type == 'image' and self.content_file and self.content_file.name:
            try:
                _ = self.content_file.storage.bucket
                return self.content_file.url
            except Exception:
                return self.content_url or ''
        
        return self.content_url or ''
    
    def approve(self, reviewer, notes=None):
        """审核通过"""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        if notes:
            self.review_notes = notes
        self.save()
    
    def reject(self, reviewer, notes=None):
        """审核拒绝"""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        if notes:
            self.review_notes = notes
        self.save()
    
    def publish(self):
        """发布内容"""
        if self.status == 'approved':
            self.status = 'published'
            self.published_at = timezone.now()
            self.save()
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

