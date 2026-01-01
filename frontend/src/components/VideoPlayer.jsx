import { useState, useEffect, useRef } from 'react';
import './VideoPlayer.css';

/**
 * MV视频播放器组件（弹窗模式）
 * 支持高级播放功能：倍速、画质切换、字幕等
 */
function VideoPlayer({ videoUrl, title, artist, onClose }) {
    const videoRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [playbackRate, setPlaybackRate] = useState(1);
    const [showControls, setShowControls] = useState(true);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const controlsTimeoutRef = useRef(null);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        // 事件监听
        const handleTimeUpdate = () => setCurrentTime(video.currentTime);
        const handleDurationChange = () => setDuration(video.duration);
        const handlePlay = () => setIsPlaying(true);
        const handlePause = () => setIsPlaying(false);
        const handleEnded = () => {
            setIsPlaying(false);
            setCurrentTime(0);
        };
        const handleVolumeChange = () => {
            setVolume(video.volume);
            setIsMuted(video.muted);
        };
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };

        video.addEventListener('timeupdate', handleTimeUpdate);
        video.addEventListener('durationchange', handleDurationChange);
        video.addEventListener('play', handlePlay);
        video.addEventListener('pause', handlePause);
        video.addEventListener('ended', handleEnded);
        video.addEventListener('volumechange', handleVolumeChange);
        document.addEventListener('fullscreenchange', handleFullscreenChange);

        // 设置初始播放速度
        video.playbackRate = playbackRate;

        return () => {
            video.removeEventListener('timeupdate', handleTimeUpdate);
            video.removeEventListener('durationchange', handleDurationChange);
            video.removeEventListener('play', handlePlay);
            video.removeEventListener('pause', handlePause);
            video.removeEventListener('ended', handleEnded);
            video.removeEventListener('volumechange', handleVolumeChange);
            document.removeEventListener('fullscreenchange', handleFullscreenChange);
        };
    }, [playbackRate]);

    useEffect(() => {
        // ESC键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                if (isFullscreen) {
                    exitFullscreen();
                } else {
                    onClose();
                }
            }
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [isFullscreen, onClose]);

    // 自动隐藏控制栏
    useEffect(() => {
        if (isPlaying) {
            const hideControls = () => {
                if (controlsTimeoutRef.current) {
                    clearTimeout(controlsTimeoutRef.current);
                }
                controlsTimeoutRef.current = setTimeout(() => {
                    setShowControls(false);
                }, 3000);
            };
            hideControls();
            const video = videoRef.current;
            if (video) {
                video.addEventListener('mousemove', hideControls);
                return () => {
                    video.removeEventListener('mousemove', hideControls);
                    if (controlsTimeoutRef.current) {
                        clearTimeout(controlsTimeoutRef.current);
                    }
                };
            }
        }
    }, [isPlaying]);

    const togglePlay = () => {
        const video = videoRef.current;
        if (!video) return;

        if (isPlaying) {
            video.pause();
        } else {
            video.play();
        }
        setShowControls(true);
    };

    const handleProgressClick = (e) => {
        const video = videoRef.current;
        if (!video) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        video.currentTime = percent * duration;
        setShowControls(true);
    };

    const handleVolumeChange = (e) => {
        const video = videoRef.current;
        if (!video) return;

        const newVolume = parseFloat(e.target.value);
        video.volume = newVolume;
        setVolume(newVolume);
        setIsMuted(newVolume === 0);
        setShowControls(true);
    };

    const toggleMute = () => {
        const video = videoRef.current;
        if (!video) return;

        video.muted = !video.muted;
        setIsMuted(video.muted);
        setShowControls(true);
    };

    const handlePlaybackRateChange = (rate) => {
        const video = videoRef.current;
        if (!video) return;

        video.playbackRate = rate;
        setPlaybackRate(rate);
        setShowSettings(false);
        setShowControls(true);
    };

    const toggleFullscreen = () => {
        const video = videoRef.current;
        if (!video) return;

        if (!isFullscreen) {
            if (video.requestFullscreen) {
                video.requestFullscreen();
            } else if (video.webkitRequestFullscreen) {
                video.webkitRequestFullscreen();
            } else if (video.mozRequestFullScreen) {
                video.mozRequestFullScreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            }
        }
        setShowControls(true);
    };

    const exitFullscreen = () => {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        }
    };

    const formatTime = (seconds) => {
        if (!isFinite(seconds) || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
    const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2];

    return (
        <div className="video-player-backdrop" onClick={handleBackdropClick}>
            <div className="video-player-container" onClick={(e) => e.stopPropagation()}>
                <button className="video-player-close" onClick={onClose}>
                    ✕
                </button>

                <div className="video-player-header">
                    <h3>{title} - {artist}</h3>
                </div>

                <div className="video-player-wrapper">
                    <video
                        ref={videoRef}
                        src={videoUrl}
                        className="video-player-video"
                        onClick={togglePlay}
                        onMouseEnter={() => setShowControls(true)}
                        onMouseLeave={() => {
                            if (isPlaying) {
                                if (controlsTimeoutRef.current) {
                                    clearTimeout(controlsTimeoutRef.current);
                                }
                                controlsTimeoutRef.current = setTimeout(() => {
                                    setShowControls(false);
                                }, 3000);
                            }
                        }}
                    >
                        您的浏览器不支持视频播放
                    </video>

                    {/* 控制栏 */}
                    <div className={`video-player-controls ${showControls ? 'show' : ''}`}>
                        {/* 进度条 */}
                        <div className="video-player-progress-container" onClick={handleProgressClick}>
                            <div className="video-player-progress-bar">
                                <div
                                    className="video-player-progress-fill"
                                    style={{ width: `${progress}%` }}
                                />
                                <div
                                    className="video-player-progress-handle"
                                    style={{ left: `${progress}%` }}
                                />
                            </div>
                        </div>

                        {/* 控制按钮 */}
                        <div className="video-player-controls-bottom">
                            <div className="video-player-controls-left">
                                <button
                                    className="video-player-btn"
                                    onClick={togglePlay}
                                    aria-label={isPlaying ? '暂停' : '播放'}
                                >
                                    {isPlaying ? '⏸' : '▶'}
                                </button>

                                <div className="video-player-time">
                                    {formatTime(currentTime)} / {formatTime(duration)}
                                </div>

                                <div className="video-player-volume-control">
                                    <button
                                        className="video-player-btn"
                                        onClick={toggleMute}
                                        aria-label={isMuted ? '取消静音' : '静音'}
                                    >
                                        {isMuted || volume === 0 ? '🔇' : volume < 0.5 ? '🔉' : '🔊'}
                                    </button>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.01"
                                        value={volume}
                                        onChange={handleVolumeChange}
                                        className="video-player-volume-slider"
                                    />
                                </div>
                            </div>

                            <div className="video-player-controls-right">
                                <div className="video-player-settings">
                                    <button
                                        className="video-player-btn"
                                        onClick={() => setShowSettings(!showSettings)}
                                        aria-label="设置"
                                    >
                                        ⚙️
                                    </button>
                                    {showSettings && (
                                        <div className="video-player-settings-menu">
                                            <div className="video-player-settings-item">
                                                <span>播放速度</span>
                                                <div className="video-player-speed-options">
                                                    {playbackRates.map(rate => (
                                                        <button
                                                            key={rate}
                                                            className={`video-player-speed-btn ${playbackRate === rate ? 'active' : ''}`}
                                                            onClick={() => handlePlaybackRateChange(rate)}
                                                        >
                                                            {rate}x
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <button
                                    className="video-player-btn"
                                    onClick={toggleFullscreen}
                                    aria-label={isFullscreen ? '退出全屏' : '全屏'}
                                >
                                    {isFullscreen ? '⤓' : '⤢'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default VideoPlayer;

