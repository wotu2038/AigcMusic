import { useState, useEffect, useRef } from 'react';
import './TreasureChest.css';

/**
 * 宝箱组件
 * 横向飘动，点击后打开展示内容
 */
function TreasureChest({ 
    content, 
    index = 0, 
    onOpen,
    delay = 0 
}) {
    const [isAnimating, setIsAnimating] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const chestRef = useRef(null);

    useEffect(() => {
        // 延迟启动动画，让多个宝箱错开
        const timer = setTimeout(() => {
            setIsAnimating(true);
        }, delay);

        return () => clearTimeout(timer);
    }, [delay]);

    const handleClick = () => {
        setIsOpen(true);
        if (onOpen) {
            onOpen(content);
        }
    };

    const getChestType = () => {
        // 根据内容类型返回不同的宝箱样式
        if (content.content_type === 'image') {
            return 'image-chest';
        } else if (content.content_type === 'text') {
            return 'text-chest';
        } else if (content.content_type === 'video') {
            return 'video-chest';
        }
        return 'default-chest';
    };

    return (
        <div 
            ref={chestRef}
            className={`treasure-chest ${getChestType()} ${isAnimating ? 'animating' : ''}`}
            style={{ 
                animationDelay: `${delay}ms`,
                '--index': index 
            }}
            onClick={handleClick}
        >
            <div className="chest-body">
                <div className="chest-lid">
                    <div className="chest-lid-top"></div>
                    <div className="chest-lid-front"></div>
                </div>
                <div className="chest-base">
                    <div className="chest-lock">
                        <div className="lock-circle"></div>
                    </div>
                    <div className="chest-decoration">
                        <div className="decoration-line"></div>
                        <div className="decoration-line"></div>
                    </div>
                </div>
            </div>
            <div className="chest-glow"></div>
            {content.content_type === 'image' && (
                <div className="chest-label">🎨 配图</div>
            )}
            {content.content_type === 'text' && (
                <div className="chest-label">💬 摘要</div>
            )}
            {content.content_type === 'video' && (
                <div className="chest-label">🎬 视频</div>
            )}
        </div>
    );
}

export default TreasureChest;

