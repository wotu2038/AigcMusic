import { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import './Player.css';

/**
 * 音乐播放器组件
 */
function Player({ song, onSongEnd }) {
    const audioRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    
    useEffect(() => {
        const audio = audioRef.current;
        if (!audio || !song) return;
        
        // 加载新歌曲
        if (song.file_url) {
            // 确保URL正确
            let audioUrl = song.file_url;
            // 如果是相对路径，Vite代理会自动处理，不需要修改
            console.log('加载音频文件:', audioUrl, '完整歌曲对象:', song);
            audio.src = audioUrl;
            audio.load();
        } else {
            console.error('歌曲没有file_url:', song);
        }
        
        // 事件监听
        const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
        const handleDurationChange = () => setDuration(audio.duration);
        const handleEnded = () => {
            setIsPlaying(false);
            setCurrentTime(0);
            if (onSongEnd) onSongEnd();
        };
        const handlePlay = () => setIsPlaying(true);
        const handlePause = () => setIsPlaying(false);
        const handleError = (e) => {
            console.error('音频加载错误:', e);
            console.error('音频错误详情:', {
                error: audio.error,
                code: audio.error?.code,
                message: audio.error?.message,
                src: audio.src
            });
            alert(`播放失败: ${audio.error?.message || '无法加载音频文件'}`);
        };
        const handleCanPlay = () => {
            console.log('音频可以播放:', song.title);
        };
        const handleLoadStart = () => {
            console.log('开始加载音频:', song.title);
        };
        const handleLoadedData = () => {
            console.log('音频数据已加载:', song.title);
        };
        const handleLoadedMetadata = () => {
            if (audio.duration && isFinite(audio.duration)) {
                setDuration(audio.duration);
            }
            console.log('音频元数据已加载:', song.title, '时长:', audio.duration);
        };
        
        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('durationchange', handleDurationChange);
        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('play', handlePlay);
        audio.addEventListener('pause', handlePause);
        audio.addEventListener('error', handleError);
        audio.addEventListener('canplay', handleCanPlay);
        audio.addEventListener('loadstart', handleLoadStart);
        audio.addEventListener('loadeddata', handleLoadedData);
        audio.addEventListener('loadedmetadata', handleLoadedMetadata);
        
        return () => {
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('durationchange', handleDurationChange);
            audio.removeEventListener('ended', handleEnded);
            audio.removeEventListener('play', handlePlay);
            audio.removeEventListener('pause', handlePause);
            audio.removeEventListener('error', handleError);
            audio.removeEventListener('canplay', handleCanPlay);
            audio.removeEventListener('loadstart', handleLoadStart);
            audio.removeEventListener('loadeddata', handleLoadedData);
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        };
    }, [song, onSongEnd]);
    
    // 播放/暂停
    const togglePlay = () => {
        const audio = audioRef.current;
        if (!audio) return;
        
        if (isPlaying) {
            audio.pause();
        } else {
            audio.play().then(() => {
                // 记录播放历史
                if (song?.song_id) {
                    recordPlayHistory();
                }
            }).catch(err => {
                console.error('播放失败:', err);
                alert('播放失败，请检查音频文件');
            });
        }
    };
    
    // 记录播放历史
    const recordPlayHistory = async () => {
        if (!song?.song_id) return;
        
        try {
            await api.post(`/songs/${song.song_id}/play/`, {
                play_duration: Math.floor(currentTime),
                play_position: Math.floor(currentTime)
            });
        } catch (err) {
            console.error('记录播放历史失败:', err);
        }
    };
    
    // 进度条点击
    const handleProgressClick = (e) => {
        const audio = audioRef.current;
        if (!audio || !duration) return;
        
        const rect = e.currentTarget.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const newTime = (clickX / rect.width) * duration;
        audio.currentTime = newTime;
        setCurrentTime(newTime);
    };
    
    // 音量控制
    const handleVolumeChange = (e) => {
        const newVolume = parseFloat(e.target.value);
        setVolume(newVolume);
        if (audioRef.current) {
            audioRef.current.volume = newVolume;
        }
        setIsMuted(newVolume === 0);
    };
    
    // 静音切换
    const toggleMute = () => {
        const audio = audioRef.current;
        if (!audio) return;
        
        if (isMuted) {
            audio.volume = volume || 0.5;
            setIsMuted(false);
        } else {
            audio.volume = 0;
            setIsMuted(true);
        }
    };
    
    // 格式化时间
    const formatTime = (seconds) => {
        if (!isFinite(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };
    
    if (!song) {
        return null;
    }
    
    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
    
    return (
        <div className="player-container">
            <audio ref={audioRef} preload="metadata" crossOrigin="anonymous" />
            
            <div className="player-info">
                <div className="player-song-info">
                    <h4 className="player-title">{song.title}</h4>
                    <p className="player-artist">{song.artist}</p>
                </div>
            </div>
            
            <div className="player-controls">
                <button
                    className="player-btn player-play-btn"
                    onClick={togglePlay}
                    aria-label={isPlaying ? '暂停' : '播放'}
                >
                    {isPlaying ? '⏸' : '▶'}
                </button>
                
                <div className="player-progress-container" onClick={handleProgressClick}>
                    <div className="player-progress-bar">
                        <div
                            className="player-progress-fill"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
                
                <div className="player-time">
                    <span>{formatTime(currentTime)}</span>
                    <span> / </span>
                    <span>{formatTime(duration)}</span>
                </div>
            </div>
            
            <div className="player-volume">
                <button
                    className="player-btn player-volume-btn"
                    onClick={toggleMute}
                    aria-label={isMuted ? '取消静音' : '静音'}
                >
                    {isMuted ? '🔇' : '🔊'}
                </button>
                <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={isMuted ? 0 : volume}
                    onChange={handleVolumeChange}
                    className="player-volume-slider"
                />
            </div>
        </div>
    );
}

export default Player;

