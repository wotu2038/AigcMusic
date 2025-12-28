"""
AIGC序列化器
"""
from rest_framework import serializers
from .models import AIGCGenerationTask, AIGCContent
from apps.songs.serializers import SongSerializer


class AIGCContentSerializer(serializers.ModelSerializer):
    """AIGC内容序列化器（用于API返回，支持Web和iOS）"""
    display_url = serializers.SerializerMethodField()
    task_type = serializers.CharField(source='task.task_type', read_only=True)
    song_id = serializers.IntegerField(source='task.song.song_id', read_only=True)
    song_title = serializers.CharField(source='task.song.title', read_only=True)
    song_artist = serializers.CharField(source='task.song.artist', read_only=True)
    
    class Meta:
        model = AIGCContent
        fields = (
            'content_id', 'content_type', 'display_url', 'content_text',
            'metadata', 'status', 'published_at', 'usage_count',
            'task_type', 'song_id', 'song_title', 'song_artist',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'content_id', 'display_url', 'usage_count', 
            'created_at', 'updated_at'
        )
    
    def get_display_url(self, obj):
        """获取内容显示URL"""
        return obj.display_url


class AIGCGenerationTaskSerializer(serializers.ModelSerializer):
    """AIGC生成任务序列化器"""
    song = SongSerializer(read_only=True)
    contents = AIGCContentSerializer(many=True, read_only=True)
    contents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AIGCGenerationTask
        fields = (
            'task_id', 'task_type', 'song', 'operator', 'status',
            'parameters', 'error_message', 'contents', 'contents_count',
            'created_at', 'completed_at'
        )
        read_only_fields = (
            'task_id', 'status', 'error_message', 
            'created_at', 'completed_at'
        )
    
    def get_contents_count(self, obj):
        """获取生成内容数量"""
        return obj.aigccontent_set.count()


class AIGCContentCreateSerializer(serializers.Serializer):
    """创建AIGC内容的序列化器（用于运营后台）"""
    task_type = serializers.ChoiceField(
        choices=['lyric_image', 'comment_summary', 'lyric_video', 'text_to_video'],
        required=True
    )
    song_id = serializers.IntegerField(required=True)
    parameters = serializers.JSONField(required=True)


class AIGCContentReviewSerializer(serializers.Serializer):
    """审核AIGC内容的序列化器"""
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        required=True
    )
    notes = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=500
    )

