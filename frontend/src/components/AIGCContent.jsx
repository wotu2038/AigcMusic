import { useState, useEffect } from 'react';
import api from '../services/api';
import Loading from './Loading';
import TreasureChest from './TreasureChest';
import TreasureModal from './TreasureModal';
import './AIGCContent.css';

/**
 * AIGC内容展示组件
 * 使用宝箱飘动的方式展示AI生成内容
 */
function AIGCContent({ songId }) {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [allContents, setAllContents] = useState([]);
    const [selectedContent, setSelectedContent] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [lyricVideos, setLyricVideos] = useState([]);

    useEffect(() => {
        if (songId) {
            loadAIGCContent();
        }
    }, [songId]);

    const loadAIGCContent = async () => {
        setLoading(true);
        setError('');

        try {
            const response = await api.get(`/songs/${songId}/aigc/`);
            const data = response.data.data || response.data;
            
            // 确保数据结构正确，合并所有内容
            if (data && typeof data === 'object') {
                const contents = [];
                
                // 添加歌词配图
                if (Array.isArray(data.lyric_images)) {
                    contents.push(...data.lyric_images);
                }
                
                // 添加评论摘要
                if (data.comment_summary) {
                    contents.push(data.comment_summary);
                }
                
                // 添加歌词视频
                if (Array.isArray(data.lyric_videos)) {
                    contents.push(...data.lyric_videos);
                    setLyricVideos(data.lyric_videos);
                }
                
                // 添加文生视频
                if (Array.isArray(data.text_to_videos)) {
                    contents.push(...data.text_to_videos);
                }
                
                setAllContents(contents);
            }
        } catch (err) {
            // 如果API不存在或没有内容，不显示错误，只是不显示内容
            // 404或其他错误都静默处理，因为不是所有歌曲都有AIGC内容
            if (err.response?.status !== 404) {
                console.log('AIGC内容加载失败:', err.response?.data?.message || err.message);
            }
            setError('');
        } finally {
            setLoading(false);
        }
    };

    const handleChestOpen = (content) => {
        setSelectedContent(content);
        setIsModalOpen(true);
    };

    const handleModalClose = () => {
        setIsModalOpen(false);
        setSelectedContent(null);
    };

    if (loading) {
        return null; // 加载时不显示，避免闪烁
    }

    // 如果没有内容，不显示组件
    if (allContents.length === 0 && lyricVideos.length === 0) {
        return null;
    }

    return (
        <>
            {/* 宝箱飘动区域 */}
            <div className="treasure-chests-container">
                {allContents.map((content, index) => (
                    <TreasureChest
                        key={content.content_id || index}
                        content={content}
                        index={index}
                        delay={index * 2000} // 每个宝箱错开2秒
                        onOpen={handleChestOpen}
                    />
                ))}
            </div>

            {/* 模态框 */}
            {isModalOpen && (
                <TreasureModal
                    content={selectedContent}
                    onClose={handleModalClose}
                />
            )}
        </>
    );
}

export default AIGCContent;

