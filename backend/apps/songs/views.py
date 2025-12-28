"""
歌曲视图
"""
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import StreamingHttpResponse, Http404
from django.db import models
from .models import Song, PlayHistory, SearchHistory
from .serializers import SongSerializer, SongListSerializer, SongListWithFileSerializer
from apps.comments.models import Comment
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def stream_audio(request, song_id):
    """流式传输音频文件（代理OSS文件，解决Content-Disposition问题）"""
    try:
        song = Song.objects.get(song_id=song_id)
        if not song.audio_file or not song.audio_file.name:
            raise Http404("音频文件不存在")
        
        # 从OSS读取文件
        audio_file = song.audio_file
        file_obj = audio_file.storage._open(audio_file.name, 'rb')
        
        # 设置响应头，允许浏览器播放
        response = StreamingHttpResponse(file_obj, content_type='audio/mpeg')
        # 设置Content-Disposition为inline，允许浏览器播放而不是下载
        response['Content-Disposition'] = 'inline'
        response['Accept-Ranges'] = 'bytes'
        # 获取文件大小
        try:
            file_size = audio_file.storage.size(audio_file.name)
            response['Content-Length'] = str(file_size)
        except:
            pass
        
        return response
    except Song.DoesNotExist:
        raise Http404("歌曲不存在")
    except Exception as e:
        logger.error(f'流式传输音频文件失败: {str(e)}')
        return Response({
            'success': False,
            'message': '音频文件加载失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SongListView(generics.ListCreateAPIView):
    """歌曲列表API"""
    queryset = Song.objects.filter(is_active=True)
    serializer_class = SongListWithFileSerializer  # 使用包含 file_url 的列表序列化器
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        keyword = self.request.query_params.get('keyword', None)
        if keyword:
            queryset = queryset.filter(
                models.Q(title__icontains=keyword) |
                models.Q(artist__icontains=keyword) |
                models.Q(album__icontains=keyword)
            )
        return queryset
    
    def list(self, request, *args, **kwargs):
        """获取列表"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # 手动分页，不使用DRF的默认分页器
        page_num = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        
        total = queryset.count()
        pages = (total + limit - 1) // limit if limit > 0 else 1
        
        start = (page_num - 1) * limit
        end = start + limit
        page_queryset = queryset[start:end]
        
        serializer = self.get_serializer(page_queryset, many=True)
        songs = serializer.data
        
        # 替换所有歌曲的 file_url 为代理URL（和详情页保持一致）
        for song in songs:
            if song.get('file_url') and song.get('song_id'):
                song['file_url'] = f'/api/songs/{song["song_id"]}/stream/'
        
        return Response({
            'success': True,
            'message': '获取成功',
            'data': {
                'songs': songs,
                'pagination': {
                    'page': page_num,
                    'limit': limit,
                    'total': total,
                    'pages': pages
                }
            }
        })


class SongDetailView(generics.RetrieveUpdateDestroyAPIView):
    """歌曲详情API"""
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'song_id'
    
    def retrieve(self, request, *args, **kwargs):
        """获取详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # 获取评论数量
        comments_count = Comment.objects.filter(song=instance, is_active=True).count()
        
        data = serializer.data
        data['comments_count'] = comments_count
        
        # 替换file_url为代理URL
        if data.get('file_url'):
            data['file_url'] = f'/api/songs/{instance.song_id}/stream/'
        
        return Response({
            'success': True,
            'message': '获取成功',
            'data': data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def play_song(request, song_id):
    """记录播放历史"""
    try:
        song = Song.objects.get(song_id=song_id)
        play_duration = request.data.get('play_duration', 0)
        play_position = request.data.get('play_position', 0)
        
        PlayHistory.objects.create(
            user=request.user,
            song=song,
            play_duration=play_duration,
            play_position=play_position
        )
        
        # 更新播放次数
        song.play_count += 1
        song.save(update_fields=['play_count'])
        
        return Response({
            'success': True,
            'message': '播放记录成功'
        })
    except Song.DoesNotExist:
        return Response({
            'success': False,
            'message': '歌曲不存在'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_song(request, song_id):
    """点赞歌曲"""
    try:
        song = Song.objects.get(song_id=song_id)
        song.like_count += 1
        song.save(update_fields=['like_count'])
        
        return Response({
            'success': True,
            'message': '点赞成功',
            'data': {
                'like_count': song.like_count
            }
        })
    except Song.DoesNotExist:
        return Response({
            'success': False,
            'message': '歌曲不存在'
        }, status=status.HTTP_404_NOT_FOUND)
