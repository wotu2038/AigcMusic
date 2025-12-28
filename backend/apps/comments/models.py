"""
评论模型
"""
from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.songs.models import Song


class Comment(models.Model):
    """评论模型"""
    comment_id = models.AutoField(primary_key=True, verbose_name='评论ID')
    content = models.TextField(verbose_name='评论内容')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', db_index=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌曲', db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, verbose_name='父评论', db_index=True)
    like_count = models.IntegerField(default=0, verbose_name='点赞数', db_index=True)
    is_active = models.BooleanField(default=True, verbose_name='是否激活', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'comments'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-like_count', '-created_at']  # 按点赞数、时间倒序
    
    def __str__(self):
        return f'{self.user.phone} - {self.content[:20]}'
    
    def get_replies(self):
        """获取回复列表"""
        return Comment.objects.filter(parent=self, is_active=True).order_by('-like_count', '-created_at')
    
    def is_liked_by_user(self, user):
        """检查用户是否已点赞此评论"""
        if not user or not user.is_authenticated:
            return False
        return UserCommentLike.objects.filter(user=user, comment=self).exists()
    
    def get_nesting_level(self):
        """获取评论的嵌套层级（0=主评论，1=回复，2=回复的回复）"""
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
            # 防止无限循环（理论上不应该发生）
            if level > 10:
                break
        return level
    
    def can_have_reply(self):
        """检查是否可以回复此评论（最多2层嵌套）"""
        return self.get_nesting_level() < 2


class UserCommentLike(models.Model):
    """用户评论点赞记录"""
    like_id = models.AutoField(primary_key=True, verbose_name='点赞ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', db_index=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='评论', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', db_index=True)
    
    class Meta:
        db_table = 'user_comment_likes'
        verbose_name = '用户评论点赞'
        verbose_name_plural = '用户评论点赞'
        unique_together = ('user', 'comment')  # 确保一个用户对一条评论只能点赞一次
        indexes = [
            models.Index(fields=['user', 'comment']),
            models.Index(fields=['comment']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.phone} - {self.comment.comment_id}'
