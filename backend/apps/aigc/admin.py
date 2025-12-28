"""
AIGC管理后台
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AIGCGenerationTask, AIGCContent


@admin.register(AIGCGenerationTask)
class AIGCGenerationTaskAdmin(admin.ModelAdmin):
    """AIGC生成任务管理"""
    list_display = (
        'task_id', 'task_type', 'song_link', 'operator', 'status', 
        'contents_count', 'created_at', 'completed_at'
    )
    list_filter = ('task_type', 'status', 'created_at')
    search_fields = ('song__title', 'song__artist', 'operator__phone')
    readonly_fields = (
        'task_id', 'status', 'error_message', 
        'created_at', 'completed_at', 'contents_display', 'parameters_example'
    )
    fieldsets = (
        ('基本信息', {
            'fields': ('task_id', 'task_type', 'song', 'operator')
        }),
        ('任务状态', {
            'fields': ('status', 'error_message', 'created_at', 'completed_at')
        }),
        ('生成参数', {
            'fields': ('parameters_example', 'parameters'),
            'description': '参数示例：<br>'
                          '<strong>歌词配图 (lyric_image):</strong><br>'
                          '<code>{"style": "beautiful", "count": 2, "lyrics_section": "chorus"}</code><br><br>'
                          '<strong>评论摘要 (comment_summary):</strong><br>'
                          '<code>{"comment_range": "hot", "summary_style": "objective"}</code><br><br>'
                              '<strong>歌词视频 (lyric_video):</strong><br>'
                              '<code>{"style": "beautiful", "duration": 5, "resolution": "720p", "use_existing_image": true}</code><br><br>'
                              '<strong>文生视频 (text_to_video):</strong><br>'
                              '<code>{"style": "beautiful", "duration": 5, "resolution": "720p", "mood": "治愈"}</code>'
        }),
        ('生成内容', {
            'fields': ('contents_display',)
        }),
    )
    
    def song_link(self, obj):
        """歌曲链接"""
        if obj.song:
            url = reverse('admin:songs_song_change', args=[obj.song.song_id])
            return format_html('<a href="{}">{}</a>', url, obj.song.title)
        return '-'
    song_link.short_description = '歌曲'
    
    def contents_count(self, obj):
        """生成内容数量"""
        return obj.aigccontent_set.count()
    contents_count.short_description = '内容数量'
    
    def parameters_example(self, obj):
        """参数示例"""
        import json
        
        # 获取当前选择的task_type（从request中获取，用于新建时）
        task_type = None
        if obj and obj.pk:
            task_type = obj.task_type
        else:
            # 新建时，尝试从request中获取
            from django.contrib.admin import site
            request = getattr(site, '_current_request', None)
            if request and request.method == 'POST':
                task_type = request.POST.get('task_type')
        
        if task_type == 'lyric_image':
            example = {
                "style": "beautiful",
                "count": 2,
                "lyrics_section": "chorus"
            }
            description = '<p><strong>歌词配图参数说明：</strong></p><ul><li>style: 图片风格（beautiful/abstract/realistic/minimalist/artistic）</li><li>count: 生成数量（1-3）</li><li>lyrics_section: 歌词段落（chorus/verse/all）</li></ul>'
        elif task_type == 'comment_summary':
            example = {
                "comment_range": "hot",
                "summary_style": "objective"
            }
            description = '<p><strong>评论摘要参数说明：</strong></p><ul><li>comment_range: 评论范围（all/hot/latest）</li><li>summary_style: 摘要风格（objective/subjective/emotional）</li></ul>'
        elif task_type == 'lyric_video':
            example = {
                "style": "beautiful",
                "duration": 5,
                "resolution": "720p",
                "use_existing_image": True
            }
            description = '<p><strong>歌词视频参数说明：</strong></p><ul><li>style: 视频风格（beautiful/abstract/realistic/minimalist/artistic）</li><li>duration: 视频时长（秒，5-10）</li><li>resolution: 分辨率（480p/720p/1080p）</li><li>use_existing_image: 是否使用已有配图（true/false）</li></ul>'
        elif task_type == 'text_to_video':
            example = {
                "style": "beautiful",
                "duration": 5,
                "resolution": "720p",
                "mood": "治愈"
            }
            description = '<p><strong>文生视频参数说明：</strong></p><ul><li>style: 视频风格（beautiful/abstract/realistic/minimalist/artistic）</li><li>duration: 视频时长（秒，5-10）</li><li>resolution: 分辨率（480p/720p/1080p）</li><li>mood: 视频氛围（治愈/激情/浪漫/宁静等）</li></ul>'
        else:
            # 默认显示两个示例
            example = {
                "提示": "请先选择任务类型，然后参考下方示例填写参数"
            }
            description = '''
            <p><strong>参数示例：</strong></p>
            <p><strong>1. 歌词配图 (lyric_image):</strong></p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{
  "style": "beautiful",
  "count": 2,
  "lyrics_section": "chorus"
}</pre>
            <p><strong>2. 评论摘要 (comment_summary):</strong></p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{
  "comment_range": "hot",
  "summary_style": "objective"
}</pre>
                <p><strong>3. 歌词视频 (lyric_video):</strong></p>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{
  "style": "beautiful",
  "duration": 5,
  "resolution": "720p",
  "use_existing_image": true
}</pre>
                <p><strong>4. 文生视频 (text_to_video):</strong></p>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{
  "style": "beautiful",
  "duration": 5,
  "resolution": "720p",
  "mood": "治愈"
}</pre>
            '''
            example_json = json.dumps(example, ensure_ascii=False, indent=2)
            return format_html(
                '<div style="background: #fff3cd; padding: 15px; border-radius: 4px; border-left: 4px solid #ffc107;">'
                '<p style="margin-top: 0;"><strong>⚠️ 请先选择任务类型</strong></p>'
                '{}</div>',
                mark_safe(description)
            )
        
        example_json = json.dumps(example, ensure_ascii=False, indent=2)
        
        return format_html(
            '<div style="background: #e7f3ff; padding: 15px; border-radius: 4px; border-left: 4px solid #2196F3;">'
            '{description}'
            '<p style="margin-bottom: 5px;"><strong>参数示例（复制使用）：</strong></p>'
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; border: 1px solid #ddd;">{example}</div>'
            '</div>',
            description=mark_safe(description),
            example=example_json
        )
    parameters_example.short_description = '参数示例（参考）'
    
    def contents_display(self, obj):
        """显示生成内容"""
        contents = obj.aigccontent_set.all()
        if not contents:
            return '暂无内容'
        
        html = '<ul>'
        for content in contents:
            url = reverse('admin:aigc_aigccontent_change', args=[content.content_id])
            status_color = {
                'pending_review': 'orange',
                'approved': 'green',
                'rejected': 'red',
                'published': 'blue'
            }.get(content.status, 'gray')
            html += f'<li><a href="{url}">内容 #{content.content_id}</a> - '
            html += f'<span style="color: {status_color}">{content.get_status_display()}</span></li>'
        html += '</ul>'
        return mark_safe(html)
    contents_display.short_description = '生成内容'
    
    def save_model(self, request, obj, form, change):
        """
        保存模型时自动触发Celery任务
        """
        # 保存任务
        super().save_model(request, obj, form, change)
        
        # 如果是新建任务（不是修改），且状态为pending，则触发Celery任务
        if not change and obj.status == 'pending':
            try:
                from .tasks import generate_aigc_content
                generate_aigc_content.delay(obj.task_id)
                self.message_user(
                    request,
                    f'任务已创建并已加入处理队列（任务ID: {obj.task_id}）',
                    level='success'
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'触发Celery任务失败: {str(e)}', exc_info=True)
                self.message_user(
                    request,
                    f'任务已创建，但触发异步任务失败: {str(e)}。请手动触发或检查Celery Worker状态。',
                    level='error'
                )


@admin.register(AIGCContent)
class AIGCContentAdmin(admin.ModelAdmin):
    """AIGC内容管理"""
    list_display = (
        'content_id', 'content_type', 'task_link', 'song_info', 
        'status', 'preview', 'usage_count', 'published_at', 'created_at'
    )
    list_filter = ('content_type', 'status', 'task__task_type', 'created_at')
    search_fields = (
        'task__song__title', 'task__song__artist', 
        'content_text', 'task__task_type'
    )
    readonly_fields = (
        'content_id', 'usage_count', 'created_at', 'updated_at',
        'content_preview', 'review_info'
    )
    fieldsets = (
        ('基本信息', {
            'fields': ('content_id', 'task', 'content_type')
        }),
        ('内容', {
            'fields': ('content_preview', 'content_url', 'content_file', 'content_text', 'metadata')
        }),
        ('状态', {
            'fields': ('status', 'review_info', 'published_at', 'usage_count')
        }),
        ('时间', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['approve_selected', 'reject_selected', 'publish_selected']
    
    def task_link(self, obj):
        """任务链接"""
        if obj.task:
            url = reverse('admin:aigc_aigcgenerationtask_change', args=[obj.task.task_id])
            return format_html('<a href="{}">任务 #{}</a>', url, obj.task.task_id)
        return '-'
    task_link.short_description = '任务'
    
    def song_info(self, obj):
        """歌曲信息"""
        if obj.task and obj.task.song:
            return f'{obj.task.song.title} - {obj.task.song.artist}'
        return '-'
    song_info.short_description = '歌曲'
    
    def preview(self, obj):
        """内容预览"""
        if obj.content_type == 'image':
            if obj.display_url:
                return format_html(
                    '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                    obj.display_url
                )
        elif obj.content_type == 'text':
            if obj.content_text:
                text = obj.content_text[:50] + '...' if len(obj.content_text) > 50 else obj.content_text
                return format_html('<div style="max-width: 200px;">{}</div>', text)
        return '-'
    preview.short_description = '预览'
    
    def content_preview(self, obj):
        """内容预览（详情页）"""
        if obj.content_type == 'image':
            if obj.display_url:
                return format_html(
                    '<img src="{}" style="max-width: 500px; max-height: 500px;" />',
                    obj.display_url
                )
        elif obj.content_type == 'text':
            if obj.content_text:
                return format_html('<div style="white-space: pre-wrap;">{}</div>', obj.content_text)
        return '暂无内容'
    content_preview.short_description = '内容预览'
    
    def review_info(self, obj):
        """审核信息"""
        if obj.reviewed_by:
            return f'{obj.reviewed_by.phone} - {obj.reviewed_at.strftime("%Y-%m-%d %H:%M")}'
        return '未审核'
    review_info.short_description = '审核信息'
    
    def approve_selected(self, request, queryset):
        """批量审核通过"""
        count = 0
        for content in queryset.filter(status='pending_review'):
            content.approve(request.user)
            count += 1
        self.message_user(request, f'成功审核通过 {count} 条内容')
    approve_selected.short_description = '审核通过选中的内容'
    
    def reject_selected(self, request, queryset):
        """批量审核拒绝"""
        count = 0
        for content in queryset.filter(status='pending_review'):
            content.reject(request.user, '批量拒绝')
            count += 1
        self.message_user(request, f'成功拒绝 {count} 条内容')
    reject_selected.short_description = '拒绝选中的内容'
    
    def publish_selected(self, request, queryset):
        """批量发布"""
        count = 0
        for content in queryset.filter(status='approved'):
            content.publish()
            count += 1
        self.message_user(request, f'成功发布 {count} 条内容')
    publish_selected.short_description = '发布选中的内容'
