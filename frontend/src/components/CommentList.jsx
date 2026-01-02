import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import authService from '../services/auth';
import CommentItem from './CommentItem';
import Loading from './Loading';
import ErrorMessage from './ErrorMessage';
import './CommentList.css';

/**
 * 评论列表组件
 */
function CommentList({ songId }) {
    const [featuredComments, setFeaturedComments] = useState([]);
    const [comments, setComments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalComments, setTotalComments] = useState(0);
    const [commentText, setCommentText] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [replyingTo, setReplyingTo] = useState(null); // 正在回复的评论ID
    const [replyText, setReplyText] = useState(''); // 回复内容
    const [submittingReply, setSubmittingReply] = useState(false);
    const currentUser = authService.getUser();
    const MAX_COMMENT_LENGTH = 140;
    
    const loadComments = useCallback(async () => {
        // 如果songId不存在，不加载评论
        if (!songId) {
            setLoading(false);
            return;
        }
        
        setLoading(true);
        setError('');
        
        try {
            const response = await api.get(`/songs/${songId}/comments/`, {
                params: { page, limit: 10 }
            });
            
            const data = response.data.data || response.data;
            setFeaturedComments(data.featured_comments || []);
            setComments(data.comments || []);
            setTotalPages(data.pagination?.pages || 1);
            // 计算总评论数（精彩评论 + 普通评论）
            const featuredCount = (data.featured_comments || []).length;
            setTotalComments(featuredCount + (data.pagination?.total || 0));
        } catch (err) {
            console.error('加载评论失败:', err);
            const errorMessage = err.response?.data?.message || err.message || '加载评论失败';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    }, [songId, page]);
    
    useEffect(() => {
        loadComments();
    }, [loadComments]);
    
    const handleSubmitComment = async (e) => {
        e.preventDefault();
        
        if (!authService.isAuthenticated()) {
            alert('请先登录后再发表评论');
            window.location.href = '/login';
            return;
        }
        
        if (!commentText.trim()) {
            setError('评论内容不能为空');
            return;
        }
        
        if (commentText.length > MAX_COMMENT_LENGTH) {
            setError(`评论内容不能超过${MAX_COMMENT_LENGTH}字`);
            return;
        }
        
        setSubmitting(true);
        setError('');
        
        try {
            const response = await api.post(`/songs/${songId}/comments/create/`, {
                content: commentText.trim()
            });
            
            // 添加新评论后，重新加载评论列表以更新精彩评论
            const hasAI = commentText.includes('@AI');
            setCommentText('');
            // 重新加载评论列表，更新精彩评论
            await loadComments();
            
            // 如果包含@AI，设置定时器自动刷新（等待AI回复生成）
            if (hasAI) {
                // 延迟刷新，给AI生成时间（5秒后开始刷新，每3秒刷新一次，最多刷新5次）
                let refreshCount = 0;
                const refreshInterval = setInterval(async () => {
                    refreshCount++;
                    await loadComments();
                    if (refreshCount >= 5) {
                        clearInterval(refreshInterval);
                    }
                }, 3000);
                
                // 5秒后开始第一次刷新
                setTimeout(async () => {
                    if (refreshCount === 0) {
                        await loadComments();
                    }
                }, 5000);
            }
        } catch (err) {
            setError(err.response?.data?.message || '发表评论失败');
        } finally {
            setSubmitting(false);
        }
    };
    
    const handleDeleteComment = async (commentId) => {
        if (!window.confirm('确定要删除这条评论吗？')) {
            return;
        }
        
        try {
            await api.delete(`/comments/${commentId}/delete/`);
            // 从列表中移除（包括精彩评论和普通评论）
            setFeaturedComments(prev => prev.filter(c => c.comment_id !== commentId));
            setComments(prev => prev.filter(c => c.comment_id !== commentId));
        } catch (err) {
            alert(err.response?.data?.message || '删除评论失败');
        }
    };
    
    const handleLikeComment = async (commentId) => {
        if (!authService.isAuthenticated()) {
            alert('请先登录后再点赞评论');
            window.location.href = '/login';
            return;
        }
        
        try {
            const response = await api.post(`/comments/${commentId}/like/`);
            const data = response.data.data || response.data;
            
            // 递归更新回复的点赞状态（包括嵌套回复）
            const updateReply = (reply) => {
                if (reply.comment_id === commentId) {
                    return { ...reply, like_count: data.like_count, is_liked: data.is_liked };
                }
                // 检查嵌套回复
                if (reply.replies && Array.isArray(reply.replies)) {
                    const updatedNestedReplies = reply.replies.map(updateReply);
                    const hasNestedUpdate = updatedNestedReplies.some((nr, idx) => 
                        nr.comment_id === commentId || 
                        (reply.replies[idx].like_count !== nr.like_count || reply.replies[idx].is_liked !== nr.is_liked)
                    );
                    if (hasNestedUpdate) {
                        return { ...reply, replies: updatedNestedReplies };
                    }
                }
                return reply;
            };
            
            // 更新评论的点赞数和点赞状态（包括精彩评论和普通评论）
            const updateComment = (c) => {
                // 检查是否是主评论
                if (c.comment_id === commentId) {
                    return { ...c, like_count: data.like_count, is_liked: data.is_liked };
                }
                // 检查是否是回复（包括嵌套回复）
                if (c.replies && Array.isArray(c.replies)) {
                    const updatedReplies = c.replies.map(updateReply);
                    // 如果回复有更新，返回更新后的评论
                    const hasUpdate = updatedReplies.some((r, idx) => 
                        r.comment_id === commentId || 
                        (c.replies[idx].like_count !== r.like_count || c.replies[idx].is_liked !== r.is_liked) ||
                        (r.replies && c.replies[idx].replies && 
                         JSON.stringify(r.replies) !== JSON.stringify(c.replies[idx].replies))
                    );
                    if (hasUpdate) {
                        return { ...c, replies: updatedReplies };
                    }
                }
                return c;
            };
            
            setFeaturedComments(prev => prev.map(updateComment));
            setComments(prev => prev.map(updateComment));
        } catch (err) {
            console.error('点赞失败:', err);
        }
    };
    
    const handleReplyComment = (comment) => {
        // 设置正在回复的评论
        setReplyingTo(comment.comment_id);
        setReplyText('');
    };
    
    const handleCancelReply = () => {
        setReplyingTo(null);
        setReplyText('');
    };
    
    const handleSubmitReply = async (e, parentCommentId) => {
        e.preventDefault();
        
        if (!authService.isAuthenticated()) {
            alert('请先登录后再回复评论');
            window.location.href = '/login';
            return;
        }
        
        if (!replyText.trim()) {
            setError('回复内容不能为空');
            return;
        }
        
        if (replyText.length > MAX_COMMENT_LENGTH) {
            setError(`回复内容不能超过${MAX_COMMENT_LENGTH}字`);
            return;
        }
        
        setSubmittingReply(true);
        setError('');
        
        try {
            const response = await api.post(`/songs/${songId}/comments/create/`, {
                content: replyText.trim(),
                parent: parentCommentId
            });
            
            // 重新加载评论列表以更新回复
            const hasAI = replyText.includes('@AI');
            await loadComments();
            setReplyingTo(null);
            setReplyText('');
            
            // 如果包含@AI，设置定时器自动刷新（等待AI回复生成）
            if (hasAI) {
                // 延迟刷新，给AI生成时间（5秒后开始刷新，每3秒刷新一次，最多刷新5次）
                let refreshCount = 0;
                const refreshInterval = setInterval(async () => {
                    refreshCount++;
                    await loadComments();
                    if (refreshCount >= 5) {
                        clearInterval(refreshInterval);
                    }
                }, 3000);
                
                // 5秒后开始第一次刷新
                setTimeout(async () => {
                    if (refreshCount === 0) {
                        await loadComments();
                    }
                }, 5000);
            }
        } catch (err) {
            setError(err.response?.data?.message || '回复失败');
        } finally {
            setSubmittingReply(false);
        }
    };
    
    const handleDeleteReply = async (replyId, parentCommentId) => {
        if (!window.confirm('确定要删除这条回复吗？')) {
            return;
        }
        
        try {
            await api.delete(`/comments/${replyId}/delete/`);
            // 重新加载评论列表以更新回复
            await loadComments();
        } catch (err) {
            alert(err.response?.data?.message || '删除回复失败');
        }
    };
    
    if (loading && comments.length === 0) {
        return <Loading text="加载评论中..." />;
    }
    
    // 获取用户头像
    const getUserAvatar = () => {
        if (currentUser?.avatar_url) {
            return <img src={currentUser.avatar_url} alt="头像" className="comment-input-avatar" />;
        }
        const initial = (currentUser?.nickname || currentUser?.phone || 'U').charAt(0).toUpperCase();
        return <div className="comment-input-avatar comment-input-avatar-placeholder">{initial}</div>;
    };
    
    const remainingChars = MAX_COMMENT_LENGTH - commentText.length;
    
    return (
        <div className="comment-list-container">
            <h3>评论 <span className="comment-count-badge">共{totalComments}条评论</span></h3>
            
            <ErrorMessage message={error} onClose={() => setError('')} />
            
            {/* 发表评论表单 */}
            {authService.isAuthenticated() ? (
                <form onSubmit={handleSubmitComment} className="comment-form">
                    <div className="comment-input-wrapper">
                        {getUserAvatar()}
                        <div className="comment-input-container">
                            <textarea
                                value={commentText}
                                onChange={(e) => setCommentText(e.target.value)}
                                placeholder="@AI 试一试AI评论"
                                className="comment-input"
                                rows="3"
                                disabled={submitting}
                                maxLength={MAX_COMMENT_LENGTH}
                            />
                            <div className="comment-input-footer">
                                <div className="comment-input-actions">
                                    <span className={`comment-char-count ${remainingChars < 20 ? 'comment-char-count-warning' : ''}`}>
                                        {remainingChars}
                                    </span>
                                    <button
                                        type="submit"
                                        className="btn btn-primary comment-submit-btn"
                                        disabled={submitting || !commentText.trim()}
                                    >
                                        {submitting ? '发表中...' : '评论'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
            ) : (
                <div className="comment-login-prompt">
                    <p>请先<a href="/login">登录</a>后再发表评论</p>
                </div>
            )}
            
            {/* 精彩评论分区 */}
            {featuredComments.length > 0 && (
                <div className="featured-comments-section">
                    <h4 className="featured-comments-title">精彩评论</h4>
                    <div className="featured-comments-list">
                        {featuredComments.map(comment => (
                            <CommentItem
                                key={comment.comment_id}
                                comment={comment}
                                onDelete={handleDeleteComment}
                                onLike={handleLikeComment}
                                onReply={handleReplyComment}
                                onDeleteReply={handleDeleteReply}
                                replyingTo={replyingTo}
                                replyText={replyText}
                                onReplyTextChange={setReplyText}
                                onSubmitReply={handleSubmitReply}
                                onCancelReply={handleCancelReply}
                                submittingReply={submittingReply}
                                songId={songId}
                                isFeatured={true}
                            />
                        ))}
                    </div>
                </div>
            )}
            
            {/* 最新评论分区 */}
            <div className="latest-comments-section">
                <h4 className="latest-comments-title">最新评论({totalComments})</h4>
                <div className="comments-list">
                    {comments.length > 0 ? (
                    comments.map(comment => (
                        <CommentItem
                            key={comment.comment_id}
                            comment={comment}
                            onDelete={handleDeleteComment}
                            onLike={handleLikeComment}
                            onReply={handleReplyComment}
                            onDeleteReply={handleDeleteReply}
                            replyingTo={replyingTo}
                            replyText={replyText}
                            onReplyTextChange={setReplyText}
                            onSubmitReply={handleSubmitReply}
                            onCancelReply={handleCancelReply}
                            submittingReply={submittingReply}
                            songId={songId}
                        />
                    ))
                    ) : (
                        <div className="empty-comments">
                            <p>暂无评论，快来发表第一条评论吧！</p>
                        </div>
                    )}
                </div>
            </div>
            
            {/* 分页 */}
            {totalPages > 1 && (
                <div className="comment-pagination">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="btn btn-secondary"
                    >
                        上一页
                    </button>
                    <span className="pagination-info">
                        {page} / {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="btn btn-secondary"
                    >
                        下一页
                    </button>
                </div>
            )}
        </div>
    );
}

export default CommentList;

