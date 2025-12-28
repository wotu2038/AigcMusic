import { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import './InlinePlayer.css';

/**
 * 内联播放器组件（用于列表中的每行）
 */
function InlinePlayer({ song }) {
    const {
        isPlaying,
        currentTime,
        duration,
        volume,
        playbackRate,
        togglePlay,
        seekTo,
        setVolume,
        setPlaybackRate,
        audioRef
    } = useAudioPlayer(song);

    const [showMenu, setShowMenu] = useState(false);
    const [showSpeedMenu, setShowSpeedMenu] = useState(false);
    const menuRef = useRef(null);
    const containerRef = useRef(null);

    // 点击外部关闭菜单
    useEffect(() => {
        if (!showMenu) return;

        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowMenu(false);
                setShowSpeedMenu(false);
            }
        };

        // 使用捕获阶段，确保在其他事件之前处理
        document.addEventListener('mousedown', handleClickOutside, true);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside, true);
        };
    }, [showMenu]);

    // 计算菜单位置
    useEffect(() => {
        if (!showMenu || !menuRef.current) return;

        const updatePosition = () => {
            const menuBtn = menuRef.current.querySelector('.inline-menu-btn');
            const dropdown = menuRef.current.querySelector('.inline-menu-dropdown');
            if (!menuBtn || !dropdown) return;

            const rect = menuBtn.getBoundingClientRect();
            dropdown.style.top = `${rect.bottom + window.scrollY + 4}px`;
            dropdown.style.left = `${rect.left + window.scrollX}px`;
            dropdown.style.right = 'auto';
        };

        updatePosition();
        window.addEventListener('scroll', updatePosition);
        window.addEventListener('resize', updatePosition);

        return () => {
            window.removeEventListener('scroll', updatePosition);
            window.removeEventListener('resize', updatePosition);
        };
    }, [showMenu]);

    // 计算速度菜单位置
    useEffect(() => {
        if (!showSpeedMenu || !menuRef.current) return;

        const updatePosition = () => {
            const speedBtn = menuRef.current.querySelector('.inline-menu-item-container .inline-menu-item');
            const speedMenu = menuRef.current.querySelector('.inline-speed-menu');
            if (!speedBtn || !speedMenu) return;

            const rect = speedBtn.getBoundingClientRect();
            speedMenu.style.top = `${rect.top + window.scrollY}px`;
            speedMenu.style.left = `${rect.right + window.scrollX + 4}px`;
        };

        updatePosition();
        window.addEventListener('scroll', updatePosition);
        window.addEventListener('resize', updatePosition);

        return () => {
            window.removeEventListener('scroll', updatePosition);
            window.removeEventListener('resize', updatePosition);
        };
    }, [showSpeedMenu]);

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

    // 播放时记录历史
    useEffect(() => {
        if (isPlaying && song?.song_id) {
            recordPlayHistory();
        }
    }, [isPlaying]);

    const handleProgressClick = (e) => {
        if (!duration) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        const newTime = percentage * duration;
        seekTo(newTime);
    };

    const handleVolumeChange = (e) => {
        const newVolume = parseFloat(e.target.value);
        setVolume(newVolume);
    };

    const handleDownload = () => {
        if (!song.file_url) return;
        const link = document.createElement('a');
        link.href = song.file_url;
        link.download = `${song.title || 'song'}.mp3`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setShowMenu(false);
    };

    const handleSpeedChange = (speed) => {
        setPlaybackRate(speed);
        setShowSpeedMenu(false);
        setShowMenu(false);
    };

    const formatTime = (seconds) => {
        if (!isFinite(seconds) || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (!song) return null;

    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

    return (
        <div 
            ref={containerRef}
            className="inline-player"
            onMouseDown={(e) => {
                // 阻止播放器容器的所有鼠标事件冒泡
                e.stopPropagation();
            }}
            onClick={(e) => {
                // 阻止播放器容器的点击事件冒泡到表格行
                e.stopPropagation();
            }}
        >
            <audio ref={audioRef} />
            <button 
                className="inline-play-btn"
                onClick={(e) => {
                    e.stopPropagation();
                    togglePlay();
                }}
                title={isPlaying ? '暂停' : '播放'}
            >
                {isPlaying ? '⏸' : '▶'}
            </button>
            
            <div 
                className="inline-progress-container" 
                onClick={handleProgressClick}
            >
                <div className="inline-progress-bar">
                    <div 
                        className="inline-progress-fill"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>
            
            <span className="inline-time">
                {formatTime(currentTime)} / {formatTime(duration)}
            </span>
            
            <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={volume}
                onChange={handleVolumeChange}
                className="inline-volume"
                title="音量"
            />
            
            <div className="inline-menu-container" ref={menuRef}>
                <button 
                    className="inline-menu-btn"
                    onClick={(e) => {
                        e.stopPropagation();
                        setShowMenu(!showMenu);
                        if (showMenu) setShowSpeedMenu(false);
                    }}
                    title="更多选项"
                >
                    ⋮
                </button>
                
                {showMenu && (
                    <div className="inline-menu-dropdown">
                        <button 
                            className="inline-menu-item"
                            onClick={(e) => {
                                e.stopPropagation();
                                handleDownload();
                            }}
                        >
                            <span>⬇</span> 下载
                        </button>
                        <div className="inline-menu-item-container">
                            <button 
                                className="inline-menu-item"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowSpeedMenu(!showSpeedMenu);
                                }}
                            >
                                <span>⚡</span> 播放速度
                            </button>
                            {showSpeedMenu && (
                                <div className="inline-speed-menu">
                                    <button onClick={(e) => { e.stopPropagation(); handleSpeedChange(0.5); }} className={playbackRate === 0.5 ? 'active' : ''}>0.5</button>
                                    <button onClick={(e) => { e.stopPropagation(); handleSpeedChange(0.75); }} className={playbackRate === 0.75 ? 'active' : ''}>0.75</button>
                                    <button onClick={(e) => { e.stopPropagation(); handleSpeedChange(1); }} className={playbackRate === 1 ? 'active' : ''}>正常</button>
                                    <button onClick={(e) => { e.stopPropagation(); handleSpeedChange(1.25); }} className={playbackRate === 1.25 ? 'active' : ''}>1.25</button>
                                    <button onClick={(e) => { e.stopPropagation(); handleSpeedChange(1.5); }} className={playbackRate === 1.5 ? 'active' : ''}>1.5</button>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default InlinePlayer;
