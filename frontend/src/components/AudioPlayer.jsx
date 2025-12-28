import { useState, useEffect, useRef } from 'react';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import './AudioPlayer.css';

/**
 * 统一音频播放器组件
 * 用于列表页和详情页
 * 
 * 特性：
 * - 播放进度、播放状态：全局共享（同一首歌在不同页面一致）
 * - 音量、播放速度、循环设置：每首歌独立偏好
 */
function AudioPlayer({ song, variant = 'inline' }) {
    const {
        isPlaying,
        currentTime,
        duration,
        volume, // 该歌曲的音量偏好（如果正在播放，是当前值；否则是保存的偏好）
        playbackRate, // 该歌曲的播放速度偏好
        loop, // 该歌曲的循环设置偏好
        isCurrentSong, // 是否正在播放当前歌曲
        togglePlay,
        seekTo,
        setVolume,
        setPlaybackRate,
        toggleLoop
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

        document.addEventListener('mousedown', handleClickOutside, true);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside, true);
        };
    }, [showMenu]);

    // 计算菜单位置
    useEffect(() => {
        if (!showMenu || !menuRef.current) return;

        const updatePosition = () => {
            const menuBtn = menuRef.current.querySelector('.audio-player-menu-btn');
            const dropdown = menuRef.current.querySelector('.audio-player-menu-dropdown');
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
            const speedBtn = menuRef.current.querySelector('.audio-player-menu-item-container .audio-player-menu-item');
            const speedMenu = menuRef.current.querySelector('.audio-player-speed-menu');
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

    const handleProgressClick = (e) => {
        // 使用 displayDuration 而不是 duration，确保即使 duration 为 0 也能点击
        const effectiveDuration = duration > 0 ? duration : (song.duration || 0);
        if (!effectiveDuration) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        const newTime = percentage * effectiveDuration;
        seekTo(newTime);
    };

    const handleVolumeChange = (e) => {
        const newVolume = parseFloat(e.target.value);
        // 更新该歌曲的音量偏好（如果正在播放，会更新Audio元素；否则只保存偏好）
        setVolume(newVolume);
    };

    const handleDownload = () => {
        if (!song?.file_url) return;
        const link = document.createElement('a');
        link.href = song.file_url;
        link.download = `${song.title || 'song'}.mp3`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setShowMenu(false);
    };

    const handleSpeedChange = (speed) => {
        // 更新该歌曲的播放速度偏好（如果正在播放，会更新Audio元素；否则只保存偏好）
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

    // 如果 duration 为 0，尝试使用 song.duration 或 song.formatted_duration 作为后备
    // 优先使用 song.duration（秒数），如果没有则使用 song.formatted_duration（字符串）
    const displayDuration = duration > 0 ? duration : (song.duration || 0);
    const displayDurationText = duration > 0 
        ? formatTime(duration) 
        : (song.formatted_duration || formatTime(song.duration || 0));
    
    const progress = displayDuration > 0 ? (currentTime / displayDuration) * 100 : 0;

    return (
        <div 
            ref={containerRef}
            className={`audio-player audio-player-${variant}`}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
        >
            <button 
                className="audio-player-play-btn"
                onClick={(e) => {
                    e.stopPropagation();
                    togglePlay();
                }}
                title={isPlaying ? '暂停' : '播放'}
            >
                {isPlaying ? '⏸' : '▶'}
            </button>
            
            <div 
                className="audio-player-progress-container" 
                onClick={handleProgressClick}
            >
                <div className="audio-player-progress-bar">
                    <div 
                        className="audio-player-progress-fill"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>
            
            <span className="audio-player-time">
                {formatTime(currentTime)} / {displayDurationText}
            </span>
            
            <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={volume} // 显示该歌曲的音量偏好
                onChange={handleVolumeChange}
                className="audio-player-volume"
                title="音量"
                onMouseDown={(e) => e.stopPropagation()}
                onMouseUp={(e) => e.stopPropagation()}
                onClick={(e) => e.stopPropagation()}
                onInput={(e) => e.stopPropagation()}
            />
            
            <div className="audio-player-menu-container" ref={menuRef}>
                <button 
                    className="audio-player-menu-btn"
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
                    <div className="audio-player-menu-dropdown">
                        <button 
                            className="audio-player-menu-item"
                            onClick={(e) => {
                                e.stopPropagation();
                                handleDownload();
                            }}
                        >
                            <span>⬇</span> 下载
                        </button>
                        <div className="audio-player-menu-item-container">
                            <button 
                                className="audio-player-menu-item"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowSpeedMenu(!showSpeedMenu);
                                }}
                            >
                                <span>⚡</span> 播放速度
                            </button>
                            {showSpeedMenu && (
                                <div className="audio-player-speed-menu">
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); handleSpeedChange(0.5); }} 
                                        className={playbackRate === 0.5 ? 'active' : ''}
                                    >
                                        0.5
                                    </button>
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); handleSpeedChange(0.75); }} 
                                        className={playbackRate === 0.75 ? 'active' : ''}
                                    >
                                        0.75
                                    </button>
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); handleSpeedChange(1); }} 
                                        className={playbackRate === 1 ? 'active' : ''}
                                    >
                                        正常
                                    </button>
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); handleSpeedChange(1.25); }} 
                                        className={playbackRate === 1.25 ? 'active' : ''}
                                    >
                                        1.25
                                    </button>
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); handleSpeedChange(1.5); }} 
                                        className={playbackRate === 1.5 ? 'active' : ''}
                                    >
                                        1.5
                                    </button>
                                </div>
                            )}
                        </div>
                        <button 
                            className={`audio-player-menu-item ${loop ? 'active' : ''}`}
                            onClick={(e) => {
                                e.stopPropagation();
                                toggleLoop();
                            }}
                        >
                            <span>🔁</span> 单曲循环 {loop ? '✓' : ''}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AudioPlayer;
