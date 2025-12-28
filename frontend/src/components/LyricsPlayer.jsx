import { useState, useEffect, useRef } from 'react';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import { parseLyrics, findCurrentLyricIndex } from '../utils/lyricsParser';
import './LyricsPlayer.css';

/**
 * 歌词播放器组件
 * 支持 LRC 格式和纯文本格式
 * 特性：
 * - 自动检测歌词格式
 * - LRC 格式：时间轴高亮、自动滚动、点击跳转
 * - 纯文本格式：简单显示
 */
function LyricsPlayer({ song, lyrics }) {
    const {
        currentTime,
        duration,
        isPlaying,
        seekTo,
        isCurrentSong
    } = useAudioPlayer(song);
    
    const [parsedLyrics, setParsedLyrics] = useState({ type: 'plain', lines: [] });
    const [currentIndex, setCurrentIndex] = useState(-1);
    const lyricsContainerRef = useRef(null);
    const currentLineRef = useRef(null);
    
    // 解析歌词
    useEffect(() => {
        if (lyrics) {
            const parsed = parseLyrics(lyrics);
            setParsedLyrics(parsed);
            setCurrentIndex(-1);
        } else {
            setParsedLyrics({ type: 'plain', lines: [] });
            setCurrentIndex(-1);
        }
    }, [lyrics]);
    
    // 更新当前歌词行索引
    useEffect(() => {
        if (!isCurrentSong) {
            // 不是当前歌曲时，清除高亮
            setCurrentIndex(-1);
            return;
        }
        
        if (parsedLyrics.type === 'lrc') {
            // LRC 模式：根据时间标签精确匹配
            if (isPlaying) {
                const index = findCurrentLyricIndex(parsedLyrics.lines, currentTime);
                setCurrentIndex(index);
            }
            // 暂停时保持当前高亮位置，不清除
        } else if (parsedLyrics.type === 'plain' && parsedLyrics.lines.length > 0) {
            // 纯文本模式：根据播放进度百分比高亮
            if (isPlaying && duration > 0) {
                const progress = currentTime / duration; // 0 到 1
                const totalLines = parsedLyrics.lines.length;
                // 根据进度计算当前应该高亮的行索引
                const index = Math.floor(progress * totalLines);
                // 确保索引在有效范围内
                setCurrentIndex(Math.min(index, totalLines - 1));
            }
            // 暂停时保持当前高亮位置，不清除
        }
    }, [currentTime, duration, parsedLyrics, isPlaying, isCurrentSong]);
    
    // 自动滚动到当前歌词行
    useEffect(() => {
        if (currentIndex >= 0 && currentLineRef.current && lyricsContainerRef.current) {
            const container = lyricsContainerRef.current;
            const lineElement = currentLineRef.current;
            
            // 计算滚动位置：让当前行位于容器顶部 30% 的位置
            const containerHeight = container.clientHeight;
            const lineTop = lineElement.offsetTop;
            const lineHeight = lineElement.offsetHeight;
            const targetScrollTop = lineTop - containerHeight * 0.3;
            
            // 平滑滚动
            container.scrollTo({
                top: Math.max(0, targetScrollTop),
                behavior: 'smooth'
            });
        }
    }, [currentIndex]);
    
    // 处理点击歌词行（仅 LRC 模式）
    const handleLineClick = (line) => {
        if (parsedLyrics.type === 'lrc' && line.time !== null) {
            seekTo(line.time);
        }
    };
    
    // 如果没有歌词
    if (!lyrics || parsedLyrics.lines.length === 0) {
        return (
            <div className="lyrics-player">
                <div className="lyrics-player-empty">
                    <p>暂无歌词</p>
                </div>
            </div>
        );
    }
    
    const isLRC = parsedLyrics.type === 'lrc';
    
    return (
        <div className="lyrics-player">
            <div 
                ref={lyricsContainerRef}
                className={`lyrics-container ${isLRC ? 'lyrics-lrc' : 'lyrics-plain'}`}
            >
                {parsedLyrics.lines.map((line, index) => {
                    // 支持 LRC 和纯文本模式的高亮
                    const isCurrent = index === currentIndex;
                    const isPast = index < currentIndex;
                    const isFuture = index > currentIndex;
                    
                    return (
                        <div
                            key={index}
                            ref={isCurrent ? currentLineRef : null}
                            className={`lyrics-line ${
                                isCurrent ? 'lyrics-line-current' : ''
                            } ${
                                isPast ? 'lyrics-line-past' : ''
                            } ${
                                isFuture ? 'lyrics-line-future' : ''
                            } ${
                                isLRC && line.time !== null ? 'lyrics-line-clickable' : ''
                            }`}
                            onClick={() => handleLineClick(line)}
                            title={isLRC && line.time !== null ? `点击跳转到 ${formatTime(line.time)}` : ''}
                        >
                            {line.text}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * 格式化时间显示
 */
function formatTime(seconds) {
    if (!isFinite(seconds) || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default LyricsPlayer;

