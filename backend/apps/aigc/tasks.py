"""
AIGC Celery异步任务
"""
import logging
import requests
from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import AIGCGenerationTask, AIGCContent
from .services.wanxiang_service import wanxiang_service
from .services.prompt_builder import PromptBuilder
from apps.comments.models import Comment
from utils.storage.oss_storage import image_storage, video_storage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_aigc_content(self, task_id: int):
    """
    生成AIGC内容的异步任务
    
    Args:
        task_id: 生成任务ID
    """
    try:
        task = AIGCGenerationTask.objects.get(task_id=task_id)
        task.status = 'processing'
        task.save(update_fields=['status'])
        
        song = task.song
        task_type = task.task_type
        parameters = task.parameters or {}
        
        if task_type == 'lyric_image':
            # 生成歌词配图
            _generate_lyric_images(task, song, parameters)
        
        elif task_type == 'comment_summary':
            # 生成评论摘要
            _generate_comment_summary(task, song, parameters)
        
        elif task_type == 'lyric_video':
            # 生成歌词视频（图生视频）
            _generate_lyric_video(task, song, parameters)
        
        elif task_type == 'text_to_video':
            # 生成文生视频（直接基于文本生成）
            _generate_text_to_video(task, song, parameters)
        
        else:
            raise ValueError(f'不支持的任务类型: {task_type}')
        
        # 标记任务完成
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at'])
        
        logger.info(f'AIGC任务 {task_id} 完成')
    
    except Exception as e:
        logger.error(f'AIGC任务 {task_id} 失败: {str(e)}', exc_info=True)
        
        # 更新任务状态
        task = AIGCGenerationTask.objects.get(task_id=task_id)
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'completed_at'])
        
        # 重试
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


def _generate_lyric_images(task: AIGCGenerationTask, song, parameters: dict):
    """生成歌词配图"""
    style = parameters.get('style', 'beautiful')
    count = parameters.get('count', 2)
    lyrics_section = parameters.get('lyrics_section', 'chorus')
    
    # 提取歌词关键段落
    lyrics = song.lyrics or ''
    lyrics_key = PromptBuilder.extract_lyrics_key_section(lyrics, lyrics_section)
    
    # 构建提示词
    prompt = PromptBuilder.build_lyric_image_prompt(
        song_title=song.title,
        artist=song.artist,
        lyrics=lyrics_key,
        style=style
    )
    
    # 调用阿里万相生成图片
    images = wanxiang_service.generate_image(prompt, style, count)
    
    # 保存生成的内容
    for idx, image_info in enumerate(images):
        image_url = image_info.get('url', '')
        metadata = image_info.get('metadata', {})
        
        if image_url:
            # 下载图片并上传到OSS
            try:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                # 生成文件名
                filename = f'aigc/images/{song.song_id}/{task.task_id}_{idx + 1}.jpg'
                
                # 保存到OSS
                content_file = ContentFile(response.content)
                image_storage.save(filename, content_file)
                
                # 创建内容记录
                AIGCContent.objects.create(
                    task=task,
                    content_type='image',
                    content_url=image_url,
                    content_file=filename,
                    metadata={
                        **metadata,
                        'style': style,
                        'lyrics_section': lyrics_section,
                        'width': 1024,
                        'height': 1024
                    },
                    status='pending_review'
                )
                
                logger.info(f'歌词配图生成成功: {filename}')
            
            except Exception as e:
                logger.error(f'下载或保存图片失败: {str(e)}')
                # 即使下载失败，也保存URL记录
                AIGCContent.objects.create(
                    task=task,
                    content_type='image',
                    content_url=image_url,
                    metadata=metadata,
                    status='pending_review'
                )


def _generate_comment_summary(task: AIGCGenerationTask, song, parameters: dict):
    """生成评论摘要"""
    comment_range = parameters.get('comment_range', 'hot')  # all, hot, latest
    
    # 获取评论
    comments_query = Comment.objects.filter(
        song=song,
        is_active=True,
        parent=None
    )
    
    # 先检查是否有评论
    total_comments = comments_query.count()
    if total_comments == 0:
        raise ValueError('该歌曲暂无评论，无法生成评论摘要')
    
    # 根据范围筛选评论
    if comment_range == 'hot':
        # 热门评论（点赞数>=5）
        comments = comments_query.filter(like_count__gte=5).order_by('-like_count', '-created_at')[:10]
        # 如果没有热门评论，降级使用全部评论
        if not comments.exists():
            logger.warning(f'歌曲 {song.title} 没有热门评论（点赞>=5），使用全部评论生成摘要')
            comments = comments_query.order_by('-like_count', '-created_at')[:10]
    elif comment_range == 'latest':
        # 最新评论
        comments = comments_query.order_by('-created_at')[:10]
    else:
        # 全部评论
        comments = comments_query.order_by('-like_count', '-created_at')[:10]
    
    # 再次检查（防止降级后仍为空）
    if not comments.exists():
        raise ValueError('该歌曲暂无有效评论，无法生成评论摘要')
    
    # 构建提示词
    prompt = PromptBuilder.build_comment_summary_prompt(
        song_title=song.title,
        artist=song.artist,
        comments=list(comments)
    )
    
    # 调用阿里万相生成文字
    summary_text = wanxiang_service.generate_text(prompt, max_tokens=300)
    
    # 保存生成的内容
    AIGCContent.objects.create(
        task=task,
        content_type='text',
        content_text=summary_text,
        metadata={
            'comment_range': comment_range,
            'comment_count': comments.count(),
            'word_count': len(summary_text)
        },
        status='pending_review'
    )
    
    logger.info(f'评论摘要生成成功: {task.task_id}')


def _generate_lyric_video(task: AIGCGenerationTask, song, parameters: dict):
    """生成歌词视频（基于已有配图）"""
    style = parameters.get('style', 'beautiful')
    duration = parameters.get('duration', 5)  # 视频时长（秒）
    resolution = parameters.get('resolution', '720p')  # 分辨率
    use_existing_image = parameters.get('use_existing_image', True)  # 是否使用已有配图
    
    # 提取歌词关键段落
    lyrics = song.lyrics or ''
    lyrics_key = PromptBuilder.extract_lyrics_key_section(lyrics, parameters.get('lyrics_section', 'chorus'))
    
    # 构建提示词
    prompt = PromptBuilder.build_lyric_video_prompt(
        song_title=song.title,
        artist=song.artist,
        lyrics=lyrics_key,
        style=style
    )
    logger.info(f'生成歌词视频Prompt: {prompt}')
    
    # 获取首帧图片
    image_url = None
    if use_existing_image:
        # 查找该歌曲已发布的配图
        existing_images = AIGCContent.objects.filter(
            task__song=song,
            task__task_type='lyric_image',
            content_type='image',
            status='published'
        ).order_by('-published_at')
        
        if existing_images.exists():
            image_content = existing_images.first()
            image_url = image_content.display_url or image_content.content_url
            logger.info(f'使用已有配图生成视频: {image_url}')
        else:
            # 如果没有已发布的配图，先生成一张
            logger.warning(f'歌曲 {song.title} 没有已发布的配图，先生成配图')
            # 创建临时配图任务（简化处理，直接生成）
            temp_task = AIGCGenerationTask.objects.create(
                task_type='lyric_image',
                song=song,
                operator=task.operator,
                parameters={'style': style, 'count': 1},
                status='processing'
            )
            try:
                _generate_lyric_images(temp_task, song, {'style': style, 'count': 1})
                temp_image = AIGCContent.objects.filter(task=temp_task, content_type='image').first()
                if temp_image:
                    image_url = temp_image.display_url or temp_image.content_url
                    logger.info(f'临时生成配图用于视频: {image_url}')
            except Exception as e:
                logger.error(f'生成临时配图失败: {str(e)}')
    
    if not image_url:
        raise ValueError('无法获取首帧图片，请先生成歌词配图或设置use_existing_image=false')
    
    # 调用阿里万相生成视频
    video_info = wanxiang_service.generate_video(
        image_url=image_url,
        prompt=prompt,
        duration=duration,
        resolution=resolution
    )
    
    # 下载视频并上传到OSS
    video_url = video_info.get('url', '')
    if not video_url:
        raise ValueError('视频生成失败，未返回视频URL')
    
    try:
        # 下载视频
        response = requests.get(video_url, timeout=120, stream=True)
        response.raise_for_status()
        
        # 生成文件名
        import uuid
        filename = f'aigc/videos/{song.song_id}/{task.task_id}.mp4'
        
        # 保存到OSS
        content_file = ContentFile(response.content)
        video_storage.save(filename, content_file)
        oss_url = video_storage.url(filename)
        
        # 创建内容记录
        AIGCContent.objects.create(
            task=task,
            content_type='video',
            content_url=oss_url,
            content_video_file=filename,
            metadata={
                **video_info.get('metadata', {}),
                'style': style,
                'original_video_url': video_url,
                'duration': duration,
                'resolution': resolution
            },
            status='pending_review'
        )
        
        logger.info(f'歌词视频生成成功: {filename}')
    
    except Exception as e:
        logger.error(f'下载或上传视频到OSS失败: {str(e)}', exc_info=True)
        # 即使OSS上传失败，也保存原始URL
        AIGCContent.objects.create(
            task=task,
            content_type='video',
            content_url=video_url,
            metadata={
                **video_info.get('metadata', {}),
                'style': style,
                'duration': duration,
                'resolution': resolution,
                'oss_upload_failed': True,
                'error': str(e)
            },
            status='pending_review'
        )
        logger.warning(f'视频已生成但OSS上传失败，使用原始URL: {video_url}')


def _generate_text_to_video(task: AIGCGenerationTask, song, parameters: dict):
    """生成文生视频（先生成图片，再用图片生成视频）"""
    style = parameters.get('style', 'beautiful')
    duration = parameters.get('duration', 5)
    resolution = parameters.get('resolution', '720p')
    mood = parameters.get('mood', '治愈')
    
    # 第一步：先生成图片（使用歌词配图功能）
    logger.info(f'文生视频：第一步，生成配图...')
    temp_image_task = AIGCGenerationTask.objects.create(
        task_type='lyric_image',
        song=song,
        operator=task.operator,
        parameters={'style': style, 'count': 1, 'lyrics_section': 'chorus'},
        status='processing'
    )
    try:
        _generate_lyric_images(temp_image_task, song, {'style': style, 'count': 1, 'lyrics_section': 'chorus'})
        temp_image = AIGCContent.objects.filter(task=temp_image_task, content_type='image').first()
        if not temp_image:
            raise ValueError('图片生成失败，无法继续生成视频')
        
        image_url = temp_image.display_url or temp_image.content_url
        logger.info(f'文生视频：配图生成成功，使用图片: {image_url[:50]}...')
    except Exception as e:
        logger.error(f'文生视频：配图生成失败: {str(e)}')
        raise ValueError(f'无法生成配图，文生视频失败: {str(e)}')
    
    # 第二步：使用生成的图片生成视频
    # 构建视频提示词
    prompt = PromptBuilder.build_text_to_video_prompt(
        song_title=song.title,
        artist=song.artist,
        lyrics=song.lyrics or '',
        style=style,
        mood=mood
    )
    
    logger.info(f'文生视频：第二步，使用配图生成视频，Prompt: {prompt[:100]}...')
    
    # 调用阿里万相生成视频（图生视频）
    video_info = wanxiang_service.generate_video(
        image_url=image_url,
        prompt=prompt,
        duration=duration,
        resolution=resolution
    )
    
    # 下载视频并上传到OSS
    video_url = video_info.get('url', '')
    if not video_url:
        raise ValueError('阿里万相文生视频成功但未返回视频URL')
    
    try:
        response = requests.get(video_url, timeout=60)  # 视频下载可能需要更长时间
        response.raise_for_status()
        
        # 生成文件名
        filename = f'aigc/videos/{song.song_id}/{task.task_id}.mp4'
        
        # 保存到OSS
        content_file = ContentFile(response.content)
        video_storage.save(filename, content_file)
        
        # 创建内容记录
        AIGCContent.objects.create(
            task=task,
            content_type='video',
            content_url=video_url,
            content_video_file=filename,
            metadata={
                **video_info.get('metadata', {}),
                'style': style,
                'mood': mood,
                'duration': duration,
                'resolution': resolution,
            },
            status='pending_review'
        )
        logger.info(f'文生视频生成成功: {filename}')
    
    except Exception as e:
        logger.error(f'下载或保存视频失败: {str(e)}')
        # 即使下载失败，也保存URL记录
        AIGCContent.objects.create(
            task=task,
            content_type='video',
            content_url=video_url,
            metadata=video_info.get('metadata', {}),
            status='pending_review'
        )

