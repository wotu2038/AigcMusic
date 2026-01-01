"""
歌曲序列化器
"""
from rest_framework import serializers
from .models import Song, PlayHistory, SearchHistory
from apps.users.serializers import UserSerializer


class SongSerializer(serializers.ModelSerializer):
    """歌曲序列化器"""
    formatted_duration = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    genre_display = serializers.CharField(source='get_genre_display', read_only=True)
    
    class Meta:
        model = Song
        fields = (
            'song_id', 'title', 'artist', 'album', 'duration', 
            'formatted_duration', 'audio_file', 'cover_image',
            'file_url', 'cover_url', 'lyrics', 'lyrics_file',
            'genre', 'genre_display', 'play_count', 'like_count', 'file_size', 
            'bitrate', 'sample_rate', 'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('song_id', 'play_count', 'like_count', 'created_at', 'updated_at')
    
    def get_formatted_duration(self, obj):
        """格式化时长"""
        return obj.format_duration()
    
    def get_file_url(self, obj):
        """获取文件URL"""
        return obj.file_url
    
    def get_cover_url(self, obj):
        """获取封面URL"""
        return obj.cover_url
    
    def get_file_size(self, obj):
        """获取文件大小"""
        return obj.file_size


class SongListSerializer(serializers.ModelSerializer):
    """歌曲列表序列化器（简化版，不包含 file_url）"""
    formatted_duration = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = (
            'song_id', 'title', 'artist', 'album', 'duration', 
            'formatted_duration', 'cover_url', 'play_count', 
            'like_count', 'created_at'
        )
    
    def get_formatted_duration(self, obj):
        """格式化时长"""
        return obj.format_duration()
    
    def get_cover_url(self, obj):
        """获取封面URL"""
        return obj.cover_url


class SongListWithFileSerializer(serializers.ModelSerializer):
    """歌曲列表序列化器（包含 file_url，不包含 lyrics）"""
    formatted_duration = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = (
            'song_id', 'title', 'artist', 'album', 'duration', 
            'formatted_duration', 'file_url', 'cover_url', 
            'play_count', 'like_count'
        )
    
    def get_formatted_duration(self, obj):
        """格式化时长"""
        return obj.format_duration()
    
    def get_file_url(self, obj):
        """获取文件URL"""
        return obj.file_url
    
    def get_cover_url(self, obj):
        """获取封面URL"""
        return obj.cover_url


class PlayHistorySerializer(serializers.ModelSerializer):
    """播放历史序列化器"""
    song = SongListWithFileSerializer(read_only=True)  # 使用包含 file_url 的序列化器
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PlayHistory
        fields = (
            'history_id', 'user', 'song', 'play_duration', 
            'play_position', 'device_info', 'ip_address', 'created_at'
        )
        read_only_fields = ('history_id', 'created_at')


class SearchHistorySerializer(serializers.ModelSerializer):
    """搜索历史序列化器"""
    
    class Meta:
        model = SearchHistory
        fields = (
            'history_id', 'user', 'keyword', 'search_type', 
            'result_count', 'created_at'
        )
        read_only_fields = ('history_id', 'created_at')

