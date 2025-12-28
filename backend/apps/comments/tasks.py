"""
评论相关Celery任务
"""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Comment
from apps.songs.models import Song
from apps.aigc.services.wanxiang_service import wanxiang_service

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def generate_ai_reply(self, comment_id: int):
    """
    生成AI回复的异步任务
    
    Args:
        comment_id: 用户评论ID
    """
    try:
        # 获取用户评论
        user_comment = Comment.objects.get(comment_id=comment_id, is_active=True)
        song = user_comment.song
        
        # 获取AI用户
        ai_user = User.objects.get(phone='ai_assistant')
        
        # 提取用户问题（去除@AI标记）
        user_content = user_comment.content
        # 移除@AI标记（不区分大小写）
        import re
        question = re.sub(r'@AI\s*', '', user_content, flags=re.IGNORECASE).strip()
        
        if not question:
            logger.warning(f'用户评论 {comment_id} 中没有有效问题')
            return
        
        # 构建提示词
        prompt = f"""你是一位音乐评论助手。基于以下歌曲信息，回答用户的问题。

歌曲信息：
- 歌曲名称：《{song.title}》
- 艺术家：{song.artist}
- 专辑：{song.album or "未知"}
{f"- 歌词：{song.lyrics[:200]}..." if song.lyrics else ""}

用户问题：{question}

请用简洁、友好的语言回答问题，控制在200字以内。如果问题与歌曲无关，可以礼貌地说明。"""

        # 调用千问大模型生成回复
        logger.info(f'开始为评论 {comment_id} 生成AI回复，问题：{question[:50]}...')
        ai_response = wanxiang_service.generate_text(prompt, max_tokens=300)
        
        if not ai_response or len(ai_response.strip()) == 0:
            logger.warning(f'AI回复生成失败，返回空内容')
            return
        
        # 创建AI回复评论
        ai_comment = Comment.objects.create(
            content=ai_response.strip(),
            user=ai_user,
            song=song,
            parent=user_comment,
            like_count=0,
            is_active=True
        )
        
        logger.info(f'AI回复生成成功，评论ID: {ai_comment.comment_id}')
        
    except Comment.DoesNotExist:
        logger.error(f'评论 {comment_id} 不存在')
    except User.DoesNotExist:
        logger.error('AI助手用户不存在，请先创建')
    except Exception as e:
        logger.error(f'生成AI回复失败: {str(e)}', exc_info=True)
        # 重试
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

