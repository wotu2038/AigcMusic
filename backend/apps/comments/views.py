"""
评论视图
"""
import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer
from apps.songs.models import Song

logger = logging.getLogger(__name__)


# ==================== API视图 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def comment_list(request, song_id):
    """获取评论列表"""
    song = get_object_or_404(Song, song_id=song_id, is_active=True)
    
    # 获取所有评论（按点赞数、时间倒序）
    all_comments = Comment.objects.filter(
        song=song, 
        is_active=True, 
        parent=None
    ).order_by('-like_count', '-created_at')
    
    # 精彩评论策略：点赞数最高的3条评论，自动获选
    featured_comments = all_comments[:3]
    featured_ids = list(featured_comments.values_list('comment_id', flat=True))
    
    # 普通评论（排除精彩评论）
    comments = all_comments.exclude(comment_id__in=featured_ids)
    
    # 分页（每页10条）
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 10))
    
    paginator = Paginator(comments, limit)
    page_obj = paginator.get_page(page)
    
    # 传递request上下文，以便序列化器可以获取当前用户信息
    featured_serializer = CommentSerializer(featured_comments, many=True, context={'request': request})
    comments_serializer = CommentSerializer(page_obj.object_list, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'message': '获取成功',
        'data': {
            'featured_comments': featured_serializer.data,
            'comments': comments_serializer.data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_prev': page_obj.has_previous(),
            }
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comment_create(request, song_id):
    """发表评论或回复"""
    song = get_object_or_404(Song, song_id=song_id, is_active=True)
    
    parent_id = request.data.get('parent', None)
    parent_comment = None
    
    # 如果指定了parent，验证parent是否存在且可以回复
    if parent_id:
        try:
            parent_comment = Comment.objects.get(comment_id=parent_id, is_active=True)
            # 验证parent是否属于同一首歌
            if parent_comment.song != song:
                return Response({
                    'success': False,
                    'message': '回复的评论不属于当前歌曲'
                }, status=status.HTTP_400_BAD_REQUEST)
            # 验证嵌套层级（最多2层）
            if not parent_comment.can_have_reply():
                return Response({
                    'success': False,
                    'message': '回复层级过深，最多支持2层嵌套'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Comment.DoesNotExist:
            return Response({
                'success': False,
                'message': '回复的评论不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CommentCreateSerializer(data={
        'content': request.data.get('content'),
        'song': song.song_id,
        'parent': parent_id
    })
    
    if serializer.is_valid():
        comment = serializer.save(user=request.user)
        
        # 检测是否包含@AI，如果包含则触发AI回复生成任务
        import re
        content = comment.content
        if re.search(r'@AI', content, re.IGNORECASE):
            try:
                from .tasks import generate_ai_reply
                # 异步生成AI回复
                generate_ai_reply.delay(comment.comment_id)
                logger.info(f'已触发AI回复生成任务，评论ID: {comment.comment_id}')
            except Exception as e:
                logger.error(f'触发AI回复生成任务失败: {str(e)}', exc_info=True)
                # 不阻塞用户评论，静默失败
        
        return Response({
            'success': True,
            'message': '评论成功' if not parent_id else '回复成功',
            'data': CommentSerializer(comment, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': '评论失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comment_like(request, comment_id):
    """点赞/取消点赞评论"""
    from .models import UserCommentLike
    
    comment = get_object_or_404(Comment, comment_id=comment_id, is_active=True)
    user = request.user
    
    # 检查用户是否已经点赞过
    like_record, created = UserCommentLike.objects.get_or_create(
        user=user,
        comment=comment
    )
    
    if created:
        # 首次点赞：点赞数+1
        comment.like_count += 1
        comment.save(update_fields=['like_count'])
        message = '点赞成功'
        is_liked = True
    else:
        # 已经点赞过：取消点赞，点赞数-1
        like_record.delete()
        comment.like_count = max(0, comment.like_count - 1)  # 确保不会小于0
        comment.save(update_fields=['like_count'])
        message = '取消点赞成功'
        is_liked = False
    
    return Response({
        'success': True,
        'message': message,
        'data': {
            'comment_id': comment.comment_id,
            'like_count': comment.like_count,
            'is_liked': is_liked
        }
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def comment_delete(request, comment_id):
    """删除评论（仅本人或管理员）"""
    comment = get_object_or_404(Comment, comment_id=comment_id)
    
    # 权限检查：仅本人或管理员可删除
    if comment.user != request.user and not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权删除此评论'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 软删除
    comment.is_active = False
    comment.save(update_fields=['is_active'])
    
    return Response({
        'success': True,
        'message': '删除成功'
    })
