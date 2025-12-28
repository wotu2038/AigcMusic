"""
AIGC视图
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import AIGCGenerationTask, AIGCContent
from .serializers import (
    AIGCContentSerializer, 
    AIGCGenerationTaskSerializer,
    AIGCContentCreateSerializer,
    AIGCContentReviewSerializer
)
from apps.songs.models import Song


# ==================== 用户API（供Web和iOS使用）====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def song_aigc_content(request, song_id):
    """
    获取歌曲的AIGC内容（供Web和iOS使用）
    
    返回已发布的AIGC内容，包括：
    - 歌词配图（lyric_image）
    - 评论摘要（comment_summary）
    """
    song = get_object_or_404(Song, song_id=song_id, is_active=True)
    
    # 获取已发布的AIGC内容
    contents = AIGCContent.objects.filter(
        task__song=song,
        status='published'
    ).select_related('task').order_by('-published_at')
    
    # 按类型分组
    lyric_images = contents.filter(content_type='image', task__task_type='lyric_image')
    comment_summaries = contents.filter(content_type='text', task__task_type='comment_summary')
    lyric_videos = contents.filter(content_type='video', task__task_type='lyric_video')
    text_to_videos = contents.filter(content_type='video', task__task_type='text_to_video')
    
    serializer = AIGCContentSerializer
    
    return Response({
        'success': True,
        'message': '获取成功',
        'data': {
            'song_id': song.song_id,
            'song_title': song.title,
            'song_artist': song.artist,
            'lyric_images': serializer(lyric_images, many=True).data,
            'comment_summary': serializer(comment_summaries.first()).data if comment_summaries.exists() else None,
            'lyric_videos': serializer(lyric_videos, many=True).data,
            'text_to_videos': serializer(text_to_videos, many=True).data
        }
    })


# ==================== 运营后台API ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_list(request):
    """
    获取生成任务列表（运营后台）
    
    支持筛选：
    - task_type: 任务类型
    - status: 任务状态
    - song_id: 歌曲ID
    """
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权访问'
        }, status=status.HTTP_403_FORBIDDEN)
    
    tasks = AIGCGenerationTask.objects.select_related('song', 'operator').prefetch_related('aigccontent_set')
    
    # 筛选
    task_type = request.query_params.get('task_type')
    task_status = request.query_params.get('status')
    song_id = request.query_params.get('song_id')
    
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    if task_status:
        tasks = tasks.filter(status=task_status)
    if song_id:
        tasks = tasks.filter(song_id=song_id)
    
    # 分页
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))
    from django.core.paginator import Paginator
    paginator = Paginator(tasks, limit)
    page_obj = paginator.get_page(page)
    
    serializer = AIGCGenerationTaskSerializer(page_obj.object_list, many=True)
    
    return Response({
        'success': True,
        'message': '获取成功',
        'data': {
            'tasks': serializer.data,
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
def task_create(request):
    """
    创建生成任务（运营后台）
    
    请求体：
    {
        "task_type": "lyric_image" | "comment_summary",
        "song_id": 1,
        "parameters": {
            "style": "beautiful",
            "count": 2,
            ...
        }
    }
    """
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权访问'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AIGCContentCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        song_id = serializer.validated_data['song_id']
        song = get_object_or_404(Song, song_id=song_id, is_active=True)
        
        # 创建任务
        task = AIGCGenerationTask.objects.create(
            task_type=serializer.validated_data['task_type'],
            song=song,
            operator=request.user,
            parameters=serializer.validated_data['parameters'],
            status='pending'
        )
        
        # 触发Celery异步任务生成内容
        from .tasks import generate_aigc_content
        generate_aigc_content.delay(task.task_id)
        
        return Response({
            'success': True,
            'message': '任务创建成功',
            'data': AIGCGenerationTaskSerializer(task).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': '任务创建失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_detail(request, task_id):
    """获取任务详情（运营后台）"""
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权访问'
        }, status=status.HTTP_403_FORBIDDEN)
    
    task = get_object_or_404(AIGCGenerationTask, task_id=task_id)
    serializer = AIGCGenerationTaskSerializer(task)
    
    return Response({
        'success': True,
        'message': '获取成功',
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def content_list(request):
    """
    获取内容列表（运营后台）
    
    支持筛选：
    - content_type: 内容类型
    - status: 内容状态
    - task_type: 任务类型
    - song_id: 歌曲ID
    """
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权访问'
        }, status=status.HTTP_403_FORBIDDEN)
    
    contents = AIGCContent.objects.select_related('task__song', 'reviewed_by')
    
    # 筛选
    content_type = request.query_params.get('content_type')
    content_status = request.query_params.get('status')
    task_type = request.query_params.get('task_type')
    song_id = request.query_params.get('song_id')
    
    if content_type:
        contents = contents.filter(content_type=content_type)
    if content_status:
        contents = contents.filter(status=content_status)
    if task_type:
        contents = contents.filter(task__task_type=task_type)
    if song_id:
        contents = contents.filter(task__song_id=song_id)
    
    # 分页
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))
    from django.core.paginator import Paginator
    paginator = Paginator(contents, limit)
    page_obj = paginator.get_page(page)
    
    serializer = AIGCContentSerializer(page_obj.object_list, many=True)
    
    return Response({
        'success': True,
        'message': '获取成功',
        'data': {
            'contents': serializer.data,
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
def content_review(request, content_id):
    """
    审核内容（运营后台）
    
    请求体：
    {
        "action": "approve" | "reject",
        "notes": "审核备注"
    }
    """
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权访问'
        }, status=status.HTTP_403_FORBIDDEN)
    
    content = get_object_or_404(AIGCContent, content_id=content_id)
    serializer = AIGCContentReviewSerializer(data=request.data)
    
    if serializer.is_valid():
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        if action == 'approve':
            content.approve(request.user, notes)
            message = '审核通过'
        else:
            content.reject(request.user, notes)
            message = '审核拒绝'
        
        return Response({
            'success': True,
            'message': message,
            'data': AIGCContentSerializer(content).data
        })
    
    return Response({
        'success': False,
        'message': '审核失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def content_publish(request, content_id):
    """发布内容（运营后台）"""
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': '无权访问'
        }, status=status.HTTP_403_FORBIDDEN)
    
    content = get_object_or_404(AIGCContent, content_id=content_id)
    
    if content.status != 'approved':
        return Response({
            'success': False,
            'message': '只能发布已审核通过的内容'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    content.publish()
    
    return Response({
        'success': True,
        'message': '发布成功',
        'data': AIGCContentSerializer(content).data
    })

