import { useEffect } from 'react';
import './TreasureModal.css';

/**
 * 宝箱内容模态框
 * 点击宝箱后展示AIGC内容
 */
function TreasureModal({ content, onClose }) {
    useEffect(() => {
        // 阻止背景滚动
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, []);

    useEffect(() => {
        // ESC键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    if (!content) return null;

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div className="treasure-modal-backdrop" onClick={handleBackdropClick}>
            <div className="treasure-modal-container">
                <button className="treasure-modal-close" onClick={onClose}>
                    ✕
                </button>
                
                <div className="treasure-modal-content">
                    {/* 标题 */}
                    <div className="treasure-modal-header">
                        {content.content_type === 'image' && (
                            <>
                                <h2>🎨 歌词配图</h2>
                                <span className="treasure-badge">AI生成</span>
                            </>
                        )}
                        {content.content_type === 'text' && (
                            <>
                                <h2>💬 AI评论摘要</h2>
                                <span className="treasure-badge">AI生成</span>
                            </>
                        )}
                        {content.content_type === 'video' && (
                            <>
                                <h2>🎬 歌词视频</h2>
                                <span className="treasure-badge">AI生成</span>
                            </>
                        )}
                    </div>

                    {/* 内容区域 */}
                    <div className="treasure-modal-body">
                        {content.content_type === 'image' && (
                            <div className="treasure-image-container">
                                <img 
                                    src={content.display_url || content.content_url} 
                                    alt="歌词配图"
                                    className="treasure-image"
                                />
                                {content.metadata && content.metadata.prompt && (
                                    <div className="treasure-image-info">
                                        <div className="treasure-info-label">生成提示词：</div>
                                        <div className="treasure-info-text">
                                            {content.metadata.prompt}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {content.content_type === 'text' && (
                            <div className="treasure-text-container">
                                <div className="treasure-text-content">
                                    {content.content_text}
                                </div>
                                {content.metadata && (
                                    <div className="treasure-text-meta">
                                        {content.metadata.comment_count && (
                                            <span>基于 {content.metadata.comment_count} 条评论生成</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {content.content_type === 'video' && (
                            <div className="treasure-video-container">
                                <video 
                                    src={content.display_url || content.content_url} 
                                    controls
                                    className="treasure-video"
                                    preload="metadata"
                                >
                                    您的浏览器不支持视频播放
                                </video>
                                {content.metadata && (
                                    <div className="treasure-video-info">
                                        {content.metadata.prompt && (
                                            <div className="treasure-info-label">生成提示词：</div>
                                        )}
                                        {content.metadata.prompt && (
                                            <div className="treasure-info-text">
                                                {content.metadata.prompt}
                                            </div>
                                        )}
                                        <div className="treasure-video-meta">
                                            {content.metadata.duration && (
                                                <span>时长: {content.metadata.duration}秒</span>
                                            )}
                                            {content.metadata.resolution && (
                                                <span>分辨率: {content.metadata.resolution}</span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default TreasureModal;

