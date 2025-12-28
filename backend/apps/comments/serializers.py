"""
评论序列化器
"""
from rest_framework import serializers
from .models import Comment
from apps.users.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_ai_generated = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = (
            'comment_id', 'content', 'user', 'song', 'parent', 
            'like_count', 'is_liked', 'is_active', 'replies', 'replies_count',
            'created_at', 'updated_at', 'is_ai_generated'
        )
        read_only_fields = ('comment_id', 'like_count', 'created_at', 'updated_at')
    
    def get_is_liked(self, obj):
        """获取当前用户是否已点赞此评论"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.is_liked_by_user(request.user)
        return False
    
    def get_is_ai_generated(self, obj):
        """判断是否为AI生成的评论"""
        return obj.user.phone == 'ai_assistant'
    
    def get_replies(self, obj):
        """获取回复列表（包括回复的回复）"""
        # 获取所有直接回复（parent=当前评论）
        direct_replies = obj.get_replies()[:10]  # 最多显示10条直接回复
        request = self.context.get('request')
        
        # 使用UserSerializer来序列化用户信息
        user_serializer = UserSerializer(context={'request': request})
        
        # 为每个回复获取其子回复（回复的回复）
        result = []
        for reply in direct_replies:
            # 序列化用户信息
            user_data = user_serializer.to_representation(reply.user)
            
            reply_data = {
                'comment_id': reply.comment_id,
                'content': reply.content,
                'user': user_data,
                'like_count': reply.like_count,
                'is_liked': reply.is_liked_by_user(request.user) if request and request.user and request.user.is_authenticated else False,
                'created_at': reply.created_at.isoformat(),
                'nesting_level': reply.get_nesting_level(),
                'can_reply': reply.can_have_reply(),
                'replies': []  # 回复的回复列表
            }
            
            # 获取回复的回复（最多5条）
            nested_replies = Comment.objects.filter(
                parent=reply, 
                is_active=True
            ).order_by('-like_count', '-created_at')[:5]
            
            reply_data['replies'] = [{
                'comment_id': nr.comment_id,
                'content': nr.content,
                'user': user_serializer.to_representation(nr.user),
                'like_count': nr.like_count,
                'is_liked': nr.is_liked_by_user(request.user) if request and request.user and request.user.is_authenticated else False,
                'is_ai_generated': nr.user.phone == 'ai_assistant',
                'created_at': nr.created_at.isoformat(),
                'nesting_level': nr.get_nesting_level(),
                'can_reply': nr.can_have_reply()
            } for nr in nested_replies]
            
            result.append(reply_data)
        
        return result
    
    def get_replies_count(self, obj):
        """获取回复数量"""
        return obj.get_replies().count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """创建评论序列化器"""
    
    class Meta:
        model = Comment
        fields = ('content', 'song', 'parent')
    
    def validate_content(self, value):
        """验证评论内容"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("评论内容不能为空")
        if len(value) > 1000:
            raise serializers.ValidationError("评论内容不能超过1000字")
        return value

