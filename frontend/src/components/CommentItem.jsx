import authService from '../services/auth';
import './CommentItem.css';

const MAX_COMMENT_LENGTH = 140;

/**
 * 回复项组件（支持嵌套）
 */
function ReplyItem({
    reply,
    parentComment,
    user,
    onLike,
    onReply,
    onDeleteReply,
    replyingTo,
    replyText,
    onReplyTextChange,
    onSubmitReply,
    onCancelReply,
    submittingReply,
    nestingLevel = 1
}) {
    const isReplyOwner = user && user.user_id === reply.user?.user_id;
    const isReplyStaff = user && user.is_staff;
    const canDeleteReply = isReplyOwner || isReplyStaff;
    const canReply = reply.can_reply !== false; // 默认允许回复，除非明确禁止
    
    // 格式化日期
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = now - date;
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            const hours = Math.floor(diffTime / (1000 * 60 * 60));
            if (hours === 0) {
                const minutes = Math.floor(diffTime / (1000 * 60));
                return minutes <= 0 ? '刚刚' : `${minutes}分钟前`;
            }
            return `${hours}小时前`;
        }
        
        if (date.getFullYear() === now.getFullYear()) {
            return date.toLocaleDateString('zh-CN', {
                month: 'long',
                day: 'numeric'
            });
        }
        
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };
    
    return (
        <div className={`comment-reply ${nestingLevel === 2 ? 'comment-reply-nested' : ''}`}>
            <div className="comment-header">
                <div className="comment-avatar comment-avatar-small">
                    {reply.user?.avatar_url ? (
                        <img src={reply.user.avatar_url} alt="头像" className="comment-avatar-img" />
                    ) : (
                        (reply.user?.nickname || reply.user?.phone || 'U').charAt(0).toUpperCase()
                    )}
                </div>
                <div className="comment-user-info">
                    <div className="comment-user-name-row">
                        <span className="comment-username">
                            {reply.user?.nickname || reply.user?.phone || '匿名用户'}
                        </span>
                        {reply.is_ai_generated && (
                            <span className="comment-ai-badge comment-ai-badge-small" title="AI助手">
                                <span className="comment-ai-icon">✓</span>
                            </span>
                        )}
                        {reply.user?.is_vip_valid && reply.user?.vip_type_display && (
                            <span className="comment-vip-badge comment-vip-badge-small">
                                <span className="comment-vip-icon">◎</span>
                                <span className="comment-vip-text">VIP</span>
                            </span>
                        )}
                    </div>
                    <span className="comment-time">
                        {formatDate(reply.created_at)}
                    </span>
                </div>
            </div>
            <div className="comment-content">
                {reply.content}
                {reply.is_ai_generated && (
                    <span className="comment-ai-label">内容由AI生成</span>
                )}
            </div>
            <div className="comment-reply-actions">
                <button
                    className={`comment-action-btn comment-like-btn ${reply.is_liked ? 'comment-like-btn-active' : ''}`}
                    onClick={() => onLike(reply.comment_id)}
                    title={reply.is_liked ? '取消点赞' : '点赞'}
                >
                    <span className="comment-like-icon">👍</span>
                    <span className="comment-like-count">({reply.like_count || 0})</span>
                </button>
                {canReply && onReply && (
                    <button
                        className="comment-action-btn comment-reply-btn"
                        onClick={() => onReply(reply)}
                        title="回复"
                    >
                        回复
                    </button>
                )}
                {canDeleteReply && onDeleteReply && (
                    <button
                        className="comment-action-btn comment-delete-btn"
                        onClick={() => onDeleteReply(reply.comment_id, parentComment.comment_id)}
                        title="删除"
                    >
                        🗑 删除
                    </button>
                )}
            </div>
            
            {/* 回复输入框（针对这个回复） */}
            {replyingTo === reply.comment_id && (
                <div className="comment-reply-form">
                    <form onSubmit={(e) => onSubmitReply(e, reply.comment_id)}>
                        <div className="comment-reply-input-wrapper">
                            <textarea
                                value={replyText}
                                onChange={(e) => onReplyTextChange(e.target.value)}
                                placeholder={`回复 ${reply.user?.nickname || reply.user?.phone || '匿名用户'}:`}
                                className="comment-reply-input"
                                rows="2"
                                disabled={submittingReply}
                                maxLength={MAX_COMMENT_LENGTH}
                            />
                            <div className="comment-reply-actions">
                                <span className={`comment-char-count ${(MAX_COMMENT_LENGTH - replyText.length) < 20 ? 'comment-char-count-warning' : ''}`}>
                                    {MAX_COMMENT_LENGTH - replyText.length}
                                </span>
                                <button
                                    type="button"
                                    className="btn btn-secondary comment-reply-cancel-btn"
                                    onClick={onCancelReply}
                                    disabled={submittingReply}
                                >
                                    取消
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary comment-reply-submit-btn"
                                    disabled={submittingReply || !replyText.trim()}
                                >
                                    {submittingReply ? '回复中...' : '回复'}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}
            
            {/* 嵌套回复列表（回复的回复） */}
            {reply.replies && reply.replies.length > 0 && (
                <div className="comment-replies comment-replies-nested">
                    {reply.replies.map(nestedReply => (
                        <ReplyItem
                            key={nestedReply.comment_id}
                            reply={nestedReply}
                            parentComment={reply}
                            user={user}
                            onLike={onLike}
                            onReply={onReply}
                            onDeleteReply={onDeleteReply}
                            replyingTo={replyingTo}
                            replyText={replyText}
                            onReplyTextChange={onReplyTextChange}
                            onSubmitReply={onSubmitReply}
                            onCancelReply={onCancelReply}
                            submittingReply={submittingReply}
                            nestingLevel={2}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

/**
 * 评论项组件
 */
function CommentItem({ 
    comment, 
    onDelete, 
    onLike, 
    onReply, 
    onDeleteReply,
    replyingTo,
    replyText,
    onReplyTextChange,
    onSubmitReply,
    onCancelReply,
    submittingReply,
    songId,
    isFeatured = false 
}) {
    const user = authService.getUser();
    const isOwner = user && user.user_id === comment.user?.user_id;
    const isStaff = user && user.is_staff;
    const canDelete = isOwner || isStaff;
    
    // 格式化日期：更友好的格式（如"2020年3月14日"）
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = now - date;
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        // 如果是今天
        if (diffDays === 0) {
            const hours = Math.floor(diffTime / (1000 * 60 * 60));
            if (hours === 0) {
                const minutes = Math.floor(diffTime / (1000 * 60));
                return minutes <= 0 ? '刚刚' : `${minutes}分钟前`;
            }
            return `${hours}小时前`;
        }
        
        // 如果是今年
        if (date.getFullYear() === now.getFullYear()) {
            return date.toLocaleDateString('zh-CN', {
                month: 'long',
                day: 'numeric'
            });
        }
        
        // 其他情况：显示完整日期
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };
    
    // 获取用户头像
    const getUserAvatar = () => {
        if (comment.user?.avatar_url) {
            return <img src={comment.user.avatar_url} alt="头像" className="comment-avatar-img" />;
        }
        const initial = (comment.user?.nickname || comment.user?.phone || 'U').charAt(0).toUpperCase();
        return initial;
    };
    
    // 获取VIP标识
    const getVipBadge = () => {
        if (comment.user?.is_vip_valid && comment.user?.vip_type_display) {
            const vipTypeMap = {
                '月度VIP': '月',
                '季度VIP': '季',
                '年度VIP': '年',
                '终身VIP': '终',
                '体验VIP': '体',
            };
            const vipShort = vipTypeMap[comment.user.vip_type_display] || 'VIP';
            return (
                <span className="comment-vip-badge">
                    <span className="comment-vip-icon">◎</span>
                    <span className="comment-vip-text">VIP·{vipShort}</span>
                </span>
            );
        }
        return null;
    };
    
    return (
        <div className={`comment-item ${isFeatured ? 'comment-item-featured' : ''}`}>
            <div className="comment-header">
                <div className="comment-avatar">
                    {comment.user?.avatar_url ? (
                        <img src={comment.user.avatar_url} alt="头像" className="comment-avatar-img" />
                    ) : (
                        getUserAvatar()
                    )}
                </div>
                <div className="comment-user-info">
                    <div className="comment-user-name-row">
                        <span className="comment-username">
                            {comment.user?.nickname || comment.user?.phone || '匿名用户'}
                        </span>
                        {comment.is_ai_generated && (
                            <span className="comment-ai-badge" title="AI助手">
                                <span className="comment-ai-icon">✓</span>
                            </span>
                        )}
                        {getVipBadge()}
                    </div>
                    <span className="comment-time">
                        {formatDate(comment.created_at)}
                    </span>
                </div>
            </div>
            
            <div className="comment-content">
                {comment.content}
                {comment.is_ai_generated && (
                    <span className="comment-ai-label">内容由AI生成</span>
                )}
            </div>
            
            <div className="comment-actions">
                <button
                    className={`comment-action-btn comment-like-btn ${comment.is_liked ? 'comment-like-btn-active' : ''}`}
                    onClick={() => onLike(comment.comment_id)}
                    title={comment.is_liked ? '取消点赞' : '点赞'}
                >
                    <span className="comment-like-icon">{comment.is_liked ? '👍' : '👍'}</span>
                    <span className="comment-like-count">({comment.like_count || 0})</span>
                </button>
                
                {onReply && (
                    <button
                        className="comment-action-btn comment-reply-btn"
                        onClick={() => onReply(comment)}
                        title="回复"
                    >
                        回复
                    </button>
                )}
                
                {canDelete && (
                    <button
                        className="comment-action-btn comment-delete-btn"
                        onClick={() => onDelete(comment.comment_id)}
                        title="删除"
                    >
                        🗑 删除
                    </button>
                )}
                
                {comment.replies_count > 0 && (
                    <span className="comment-replies-count">
                        共 {comment.replies_count} 条回复
                    </span>
                )}
            </div>
            
            {/* 回复输入框 */}
            {replyingTo === comment.comment_id && (
                <div className="comment-reply-form">
                    <form onSubmit={(e) => onSubmitReply(e, comment.comment_id)}>
                        <div className="comment-reply-input-wrapper">
                            <textarea
                                value={replyText}
                                onChange={(e) => onReplyTextChange(e.target.value)}
                                placeholder={`回复 ${comment.user?.nickname || comment.user?.phone || '匿名用户'}:`}
                                className="comment-reply-input"
                                rows="2"
                                disabled={submittingReply}
                                maxLength={MAX_COMMENT_LENGTH}
                            />
                            <div className="comment-reply-actions">
                                <span className={`comment-char-count ${(MAX_COMMENT_LENGTH - replyText.length) < 20 ? 'comment-char-count-warning' : ''}`}>
                                    {MAX_COMMENT_LENGTH - replyText.length}
                                </span>
                                <button
                                    type="button"
                                    className="btn btn-secondary comment-reply-cancel-btn"
                                    onClick={onCancelReply}
                                    disabled={submittingReply}
                                >
                                    取消
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary comment-reply-submit-btn"
                                    disabled={submittingReply || !replyText.trim()}
                                >
                                    {submittingReply ? '回复中...' : '回复'}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            )}
            
            {/* 回复列表 */}
            {comment.replies && comment.replies.length > 0 && (
                <div className="comment-replies">
                    {comment.replies.map(reply => (
                        <ReplyItem
                            key={reply.comment_id}
                            reply={reply}
                            parentComment={comment}
                            user={user}
                            onLike={onLike}
                            onReply={onReply}
                            onDeleteReply={onDeleteReply}
                            replyingTo={replyingTo}
                            replyText={replyText}
                            onReplyTextChange={onReplyTextChange}
                            onSubmitReply={onSubmitReply}
                            onCancelReply={onCancelReply}
                            submittingReply={submittingReply}
                            nestingLevel={reply.nesting_level || 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default CommentItem;

