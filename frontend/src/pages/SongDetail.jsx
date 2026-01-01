import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import AudioPlayer from '../components/AudioPlayer';
import LyricsPlayer from '../components/LyricsPlayer';
import CommentList from '../components/CommentList';
import AIGCContent from '../components/AIGCContent';
import './SongDetail.css';

function SongDetail() {
    const { id } = useParams();
    const [song, setSong] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    useEffect(() => {
        loadSong();
    }, [id]);
    
    const loadSong = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await api.get(`/songs/${id}/`);
            // 后端返回结构：{ success, message, data: {...} }
            setSong(response.data.data || response.data);
        } catch (err) {
            setError(err.response?.data?.message || '加载歌曲详情失败');
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <Loading text="加载歌曲详情..." />;
    }
    
    if (error || !song) {
        return (
            <div className="error-container">
                <ErrorMessage message={error || '歌曲不存在'} />
                <Link to="/" className="btn">返回歌曲库</Link>
            </div>
        );
    }
    
    return (
        <div className="song-detail-container">
            {/* 歌曲详情卡片 - 居中显示 */}
            <div className="song-detail-card">
                <div className="song-header">
                    <h2>{song.title} - {song.artist}</h2>
                    <Link to="/" className="back-button">返回歌曲库</Link>
                </div>
                
                {/* 主要内容区域：左右分栏 */}
                <div className="song-main-content">
                    {/* 左侧：封面、信息 */}
                    <div className="song-left-section">
                {song.cover_url && (
                    <div className="song-cover">
                        <img src={song.cover_url} alt={song.title} />
                    </div>
                )}
                
                <div className="song-meta-info">
                    {song.album && <span>专辑: {song.album}</span>}
                    <span>|</span>
                    <span>时长: {song.formatted_duration || `${Math.floor(song.duration / 60)}:${(song.duration % 60).toString().padStart(2, '0')}`}</span>
                        </div>
                    </div>
                    
                    {/* 右侧：歌词播放器 */}
                    <div className="song-right-section">
                        <LyricsPlayer song={song} lyrics={song.lyrics || ''} />
                    </div>
                </div>
                
                {/* 播放器：占据整个宽度 */}
                <div className="song-player-section">
                    <AudioPlayer song={song} variant="detail" />
                </div>
            </div>
            
            {/* AIGC内容展示 */}
            <AIGCContent songId={song.song_id} />
            
            {/* 评论列表 - 居中显示 */}
            <CommentList songId={song.song_id} />
        </div>
    );
}

export default SongDetail;

