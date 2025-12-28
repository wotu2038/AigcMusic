import { useState, useEffect, useLayoutEffect, useRef, useCallback, useMemo } from 'react';

/**
 * URL规范化工具函数
 * 将URL统一转换为绝对URL，用于比较
 */
function normalizeUrl(url) {
    if (!url) return '';
    try {
        // 如果是相对URL，转换为绝对URL
        if (url.startsWith('/')) {
            return new URL(url, window.location.origin).href;
        }
        // 如果已经是绝对URL，直接返回
        return new URL(url).href;
    } catch (e) {
        // 如果URL解析失败，返回原始值
        return url;
    }
}

/**
 * 比较两个URL是否相同（忽略协议、域名等，只比较路径）
 */
function isSameUrl(url1, url2) {
    if (!url1 || !url2) return false;
    const normalized1 = normalizeUrl(url1);
    const normalized2 = normalizeUrl(url2);
    return normalized1 === normalized2;
}

/**
 * 全局音频播放管理器（单例）
 * 管理全局唯一的Audio元素和播放状态
 * 
 * 设计原则：
 * - 播放进度、播放状态：全局共享（同一首歌在不同页面一致）
 * - 音量、播放速度、循环设置：全局统一（所有播放器共享）
 */
class AudioPlayerManager {
    constructor() {
        // 全局唯一的Audio元素
        this.audioElement = null;
        
        // 全局共享状态
        this.currentSong = null;
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        
        // 全局统一的设置（所有播放器共享）
        this.volume = 1.0;
        this.playbackRate = 1.0;
        this.loop = false;
        
        // 状态监听器集合
        this.listeners = new Set();
        
        // sessionStorage 缓存相关
        this.CACHE_KEY = 'audioPlayerState';
        this.CACHE_EXPIRY = 5 * 60 * 1000; // 5分钟过期
        this.SAVE_THROTTLE = 1000; // 1秒内最多保存一次
        this.lastSaveTime = 0;
        this._lastCachedState = null;
        this._sessionStorageAvailable = this.checkSessionStorageAvailable();
        
        // 初始化Audio元素
        this.initAudio();
        
        // 从 sessionStorage 恢复状态（如果存在）
        this.restoreFromCache();
    }

    /**
     * 检查 sessionStorage 是否可用
     */
    checkSessionStorageAvailable() {
        try {
            const test = '__sessionStorage_test__';
            sessionStorage.setItem(test, test);
            sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * 保存状态到 sessionStorage（智能缓存策略）
     */
    saveToCache() {
        if (!this._sessionStorageAvailable) return;

        const state = this.getState();
        const now = Date.now();
        
        // 节流：只保存关键状态变化
        const shouldSave = 
            now - this.lastSaveTime > this.SAVE_THROTTLE && // 节流
            (this._lastCachedState?.isPlaying !== state.isPlaying || // 播放状态变化
             this._lastCachedState?.currentSong?.song_id !== state.currentSong?.song_id); // 歌曲变化
        
        if (shouldSave) {
            try {
                const cacheData = {
                    currentSongId: state.currentSong?.song_id,
                    currentSongFileUrl: state.currentSong?.file_url,
                    currentSongTitle: state.currentSong?.title,
                    isPlaying: state.isPlaying,
                    currentTime: state.currentTime, // 保存当前时间，用于恢复
                    // 不保存 currentTime（频繁变化，恢复时从全局状态获取）
                    duration: state.duration,
                    volume: state.volume,
                    playbackRate: state.playbackRate,
                    loop: state.loop,
                    timestamp: now
                };
                
                console.log('[AudioPlayerManager] 保存状态到 sessionStorage:', {
                    songId: cacheData.currentSongId,
                    isPlaying: cacheData.isPlaying,
                    currentTime: cacheData.currentTime
                });
                
                sessionStorage.setItem(this.CACHE_KEY, JSON.stringify(cacheData));
                this.lastSaveTime = now;
                this._lastCachedState = {
                    isPlaying: state.isPlaying,
                    currentSong: state.currentSong ? { song_id: state.currentSong.song_id } : null
                };
            } catch (e) {
                console.warn('保存播放状态到 sessionStorage 失败:', e);
                // 存储失败，标记为不可用
                this._sessionStorageAvailable = false;
            }
        }
    }

    /**
     * 从 sessionStorage 恢复状态
     */
    restoreFromCache() {
        if (!this._sessionStorageAvailable) return;

        try {
            const cached = sessionStorage.getItem(this.CACHE_KEY);
            if (!cached) return;

            const cacheData = JSON.parse(cached);
            const now = Date.now();

            // 检查缓存是否过期
            if (now - cacheData.timestamp > this.CACHE_EXPIRY) {
                sessionStorage.removeItem(this.CACHE_KEY);
                return;
            }

            // 恢复 currentSong 对象（最简单的方案：直接恢复基本信息）
            if (cacheData.currentSongId && cacheData.currentSongFileUrl) {
                this.currentSong = {
                    song_id: cacheData.currentSongId,
                    file_url: cacheData.currentSongFileUrl,
                    title: cacheData.currentSongTitle
                };
                
                console.log('[AudioPlayerManager] 从缓存恢复 currentSong:', {
                    songId: this.currentSong.song_id,
                    fileUrl: this.currentSong.file_url
                });
            }

            // 恢复播放状态和设置
            this.isPlaying = cacheData.isPlaying || false;
            this.currentTime = cacheData.currentTime || 0; // 恢复当前时间
            this.volume = cacheData.volume ?? 1.0;
            this.playbackRate = cacheData.playbackRate ?? 1.0;
            this.loop = cacheData.loop ?? false;
            this.duration = cacheData.duration || 0;

            // 更新 Audio 元素
            if (this.audioElement) {
                // 注意：不在这里设置 src，避免触发错误的网络请求
                // 如果 Audio 元素已经有 src 且匹配当前歌曲，保持它
                // 否则，等到用户点击播放时再设置 src（在 togglePlay 中处理）
                const currentSrc = this.audioElement.src;
                const shouldKeepSrc = this.currentSong && 
                    currentSrc && 
                    isSameUrl(currentSrc, this.currentSong.file_url);
                
                if (!shouldKeepSrc && currentSrc) {
                    // 如果 src 不匹配，清空它（避免加载错误的音频）
                    this.audioElement.src = '';
                    console.log('[AudioPlayerManager] 清空不匹配的 Audio src');
                }
                
                this.audioElement.volume = this.volume;
                this.audioElement.playbackRate = this.playbackRate;
                this.audioElement.loop = this.loop;
                
                // 如果 Audio 元素已加载且有 currentTime，恢复它
                if (this.audioElement.readyState >= 2 && this.currentTime > 0) {
                    this.audioElement.currentTime = this.currentTime;
                    console.log('[AudioPlayerManager] 恢复 Audio 元素的 currentTime:', this.currentTime);
                }
                // 注意：不自动恢复播放，因为浏览器可能阻止自动播放
                // 用户点击播放按钮时，togglePlay 会处理播放逻辑和设置 src
            }
        } catch (e) {
            console.warn('从 sessionStorage 恢复播放状态失败:', e);
            // 恢复失败，清除缓存
            try {
                sessionStorage.removeItem(this.CACHE_KEY);
            } catch (e2) {
                // 忽略清除错误
            }
        }
    }

    /**
     * 初始化全局Audio元素
     */
    initAudio() {
        if (!this.audioElement) {
            this.audioElement = new Audio();
            this.audioElement.preload = 'metadata';
            this.audioElement.loop = this.loop;
            this.audioElement.volume = this.volume;
            this.audioElement.playbackRate = this.playbackRate;
            
            // 监听Audio事件，更新全局状态
            this.audioElement.addEventListener('timeupdate', () => {
                if (this.audioElement.readyState >= 2) {
                    this.currentTime = this.audioElement.currentTime;
                    this.notifyListeners();
                }
            });
            
            this.audioElement.addEventListener('durationchange', () => {
                if (this.audioElement.duration && isFinite(this.audioElement.duration)) {
                    this.duration = this.audioElement.duration;
                    this.notifyListeners();
                }
            });
            
            this.audioElement.addEventListener('loadedmetadata', () => {
                if (this.audioElement.duration && isFinite(this.audioElement.duration)) {
                    this.duration = this.audioElement.duration;
                    this.notifyListeners();
                }
            });
            
            this.audioElement.addEventListener('play', () => {
                this.isPlaying = true;
                this.notifyListeners();
            });
            
            this.audioElement.addEventListener('pause', () => {
                this.isPlaying = false;
                this.notifyListeners();
            });
            
            this.audioElement.addEventListener('ended', () => {
                if (!this.loop) {
                    this.isPlaying = false;
                    this.currentTime = 0;
                    this.notifyListeners();
                }
            });
            
            this.audioElement.addEventListener('error', (e) => {
                console.error('音频错误:', e, this.audioElement.error);
                this.isPlaying = false;
                this.notifyListeners();
            });
        }
    }

    /**
     * 注册状态监听器
     * @param {Function} listener - 状态变化监听器
     * @param {boolean} immediateNotify - 是否立即通知当前状态（默认true）
     */
    addListener(listener, immediateNotify = true) {
        this.listeners.add(listener);
        // 只有在需要时才立即通知
        if (immediateNotify) {
            listener(this.getState());
        }
    }

    /**
     * 移除状态监听器
     */
    removeListener(listener) {
        this.listeners.delete(listener);
    }

    /**
     * 通知所有监听器状态变化
     */
    notifyListeners() {
        const state = this.getState();
        
        // 保存到 sessionStorage（智能缓存策略）
        this.saveToCache();
        
        // 通知所有监听器
        this.listeners.forEach(listener => {
            try {
                listener(state);
            } catch (error) {
                console.error('状态监听器错误:', error);
            }
        });
    }

    /**
     * 获取当前状态
     */
    getState() {
        return {
            currentSong: this.currentSong,
            isPlaying: this.isPlaying,
            currentTime: this.currentTime,
            duration: this.duration,
            volume: this.volume,
            playbackRate: this.playbackRate,
            loop: this.loop,
            audioElement: this.audioElement
        };
    }

    /**
     * 设置当前歌曲
     * @param {Object} song - 歌曲对象
     * @param {boolean} autoPlay - 是否自动播放（如果之前正在播放）
     */
    setSong(song, autoPlay = false) {
        if (!song || !song.song_id) return;
        
        // 检查是否是同一首歌：优先比较 song_id，如果没有则比较 file_url
        let isNewSong = true;
        if (this.currentSong) {
            // 优先比较 song_id（最可靠）
            if (this.currentSong.song_id && song.song_id) {
                isNewSong = this.currentSong.song_id !== song.song_id;
            }
            // 如果 song_id 不匹配或不存在，比较 file_url
            else if (this.currentSong.file_url && song.file_url) {
                isNewSong = !isSameUrl(this.currentSong.file_url, song.file_url);
            }
            // 如果都没有，认为是新歌曲
        }
        
        console.log('[AudioPlayerManager] setSong:', {
            currentSongId: this.currentSong?.song_id,
            newSongId: song.song_id,
            currentFileUrl: this.currentSong?.file_url,
            newFileUrl: song.file_url,
            isNewSong,
            autoPlay,
            wasPlaying: this.isPlaying
        });
        
        if (isNewSong) {
            // 记录之前是否正在播放
            const wasPlaying = this.isPlaying;
            
            // 暂停旧歌曲（如果正在播放）
            if (wasPlaying && this.audioElement) {
                this.audioElement.pause();
            }
            
            // 立即重置播放进度并更新UI
            this.currentTime = 0;
            this.duration = 0;
            this.currentSong = song;
            
            // 如果Audio元素已加载，立即重置其currentTime（避免显示旧进度）
            if (this.audioElement && this.audioElement.src) {
                this.audioElement.currentTime = 0;
            }
            
            // 乐观更新：如果需要自动播放，立即设置 isPlaying = true
            // 这样UI会立即显示暂停图标，提升用户体验
            if (autoPlay && wasPlaying) {
                this.isPlaying = true; // 乐观更新，立即显示暂停图标
            } else {
                this.isPlaying = false; // 否则设置为暂停状态
            }
            
            // 立即通知监听器，更新UI显示（显示 0:00 和正确的播放状态）
            this.notifyListeners();
            
            // 如果需要自动播放，加载并播放新歌曲
            if (autoPlay && wasPlaying) {
                // 异步加载并播放，不阻塞UI更新
                this.loadAndPlayNewSong();
            }
        } else {
            // 同一首歌，只更新引用
            this.currentSong = song;
            this.notifyListeners();
        }
    }

    /**
     * 加载并播放新歌曲（内部方法）
     */
    async loadAndPlayNewSong() {
        if (!this.audioElement || !this.currentSong?.file_url) {
            return;
        }

        try {
            // 设置新歌曲的src
            this.audioElement.src = this.currentSong.file_url;
            this.audioElement.load();
            
            // 优化：使用 loadedmetadata 而不是 canplay（更快）
            // loadedmetadata 只需要加载元数据，不需要加载足够的数据来播放
            // 这样可以更快地开始播放
            await new Promise((resolve, reject) => {
                const handleLoadedMetadata = () => {
                    this.audioElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
                    this.audioElement.removeEventListener('error', handleError);
                    resolve();
                };
                const handleError = (e) => {
                    this.audioElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
                    this.audioElement.removeEventListener('error', handleError);
                    reject(e);
                };
                
                // 如果已经加载了元数据，直接resolve
                if (this.audioElement.readyState >= 1) {
                    resolve();
                } else {
                    this.audioElement.addEventListener('loadedmetadata', handleLoadedMetadata, { once: true });
                    this.audioElement.addEventListener('error', handleError, { once: true });
                }
            });
            
            // 确保播放位置为 0
            this.audioElement.currentTime = 0;
            this.currentTime = 0;
            
            // 开始播放
            await this.audioElement.play();
            // play 事件会自动设置 isPlaying = true
        } catch (err) {
            console.error('加载并播放新歌曲失败:', err);
            this.isPlaying = false;
            this.notifyListeners();
        }
    }

    /**
     * 播放/暂停
     */
    async togglePlay() {
        if (!this.audioElement || !this.currentSong?.file_url) {
            return;
        }

        if (this.isPlaying) {
            // 暂停
            this.audioElement.pause();
        } else {
            // 播放
            // 检查是否是新歌曲（通过比较 Audio 元素的 src）
            const currentAudioSrc = this.audioElement.src;
            const newSongSrc = this.currentSong.file_url;
            const isNewSongInAudio = !currentAudioSrc || 
                !isSameUrl(currentAudioSrc, newSongSrc);
            
            // 如果Audio还没有加载或者是新歌曲，先加载
            if (isNewSongInAudio || this.audioElement.readyState === 0) {
                // 新歌曲，加载并重置播放位置
                this.audioElement.src = newSongSrc;
                this.audioElement.load();
                
                // 等待加载完成
                await new Promise((resolve, reject) => {
                    const handleCanPlay = () => {
                        this.audioElement.removeEventListener('canplay', handleCanPlay);
                        this.audioElement.removeEventListener('error', handleError);
                        resolve();
                    };
                    const handleError = (e) => {
                        this.audioElement.removeEventListener('canplay', handleCanPlay);
                        this.audioElement.removeEventListener('error', handleError);
                        reject(e);
                    };
                    this.audioElement.addEventListener('canplay', handleCanPlay);
                    this.audioElement.addEventListener('error', handleError);
                });
                
                // 明确重置播放位置为 0（新歌曲从头开始）
                this.audioElement.currentTime = 0;
                this.currentTime = 0;
                this.notifyListeners(); // 确保UI更新
            } else {
                // 同一首歌，恢复播放位置（如果之前有进度）
                if (this.currentTime > 0) {
                    this.audioElement.currentTime = this.currentTime;
                }
            }
            
            try {
                await this.audioElement.play();
            } catch (err) {
                console.error('播放失败:', err);
                this.isPlaying = false;
                this.notifyListeners();
            }
        }
    }

    /**
     * 设置播放位置
     */
    seekTo(time) {
        if (this.audioElement && this.duration > 0) {
            const newTime = Math.max(0, Math.min(time, this.duration));
            this.currentTime = newTime;
            this.audioElement.currentTime = newTime;
            this.notifyListeners();
        }
    }

    /**
     * 设置音量（全局统一）
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.audioElement) {
            this.audioElement.volume = this.volume;
        }
        this.notifyListeners();
    }

    /**
     * 设置播放速度（全局统一）
     */
    setPlaybackRate(rate) {
        this.playbackRate = rate;
        if (this.audioElement) {
            this.audioElement.playbackRate = this.playbackRate;
        }
        this.notifyListeners();
    }

    /**
     * 设置循环播放（全局统一）
     */
    setLoop(loop) {
        this.loop = loop;
        if (this.audioElement) {
            this.audioElement.loop = this.loop;
        }
        this.notifyListeners();
    }

    /**
     * 切换循环播放
     */
    toggleLoop() {
        this.setLoop(!this.loop);
    }
}

// 全局单例
const manager = new AudioPlayerManager();

/**
 * 从 sessionStorage 恢复状态（辅助函数）
 */
function restoreStateFromCache() {
    try {
        const CACHE_KEY = 'audioPlayerState';
        const CACHE_EXPIRY = 5 * 60 * 1000; // 5分钟过期
        
        const cached = sessionStorage.getItem(CACHE_KEY);
        if (!cached) return null;

        const cacheData = JSON.parse(cached);
        const now = Date.now();

        // 检查缓存是否过期
        if (now - cacheData.timestamp > CACHE_EXPIRY) {
            sessionStorage.removeItem(CACHE_KEY);
            return null;
        }

        // 构建恢复的状态对象
        const restoredState = {
            currentSong: cacheData.currentSongId && cacheData.currentSongFileUrl ? {
                song_id: cacheData.currentSongId,
                file_url: cacheData.currentSongFileUrl,
                title: cacheData.currentSongTitle
            } : null,
            isPlaying: cacheData.isPlaying || false,
            currentTime: cacheData.currentTime || 0, // 恢复当前时间
            duration: cacheData.duration || 0,
            volume: cacheData.volume ?? 1.0,
            playbackRate: cacheData.playbackRate ?? 1.0,
            loop: cacheData.loop ?? false,
            audioElement: manager.audioElement
        };
        
        console.log('[restoreStateFromCache] 从 sessionStorage 恢复状态:', {
            songId: restoredState.currentSong?.song_id,
            isPlaying: restoredState.isPlaying,
            currentTime: restoredState.currentTime
        });
        
        return restoredState;
    } catch (e) {
        console.warn('从 sessionStorage 恢复状态失败:', e);
        return null;
    }
}

/**
 * 音频播放器Hook
 * 提供统一的音频播放管理，与全局状态同步
 */
export function useAudioPlayer(song) {
    // 使用 useState + useLayoutEffect 同步外部状态
    // useLayoutEffect 确保在 DOM 更新之前同步状态，避免闪烁
    // 注意：useState 初始化时直接使用全局状态，因为全局状态是最准确的
    const [state, setState] = useState(() => manager.getState());
    const stateRef = useRef(state);
    const listenerRef = useRef(null);

    // 更新本地状态引用
    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    // 使用 useLayoutEffect 确保组件挂载时立即同步状态（在 DOM 更新之前）
    // 这确保了从详情页返回列表页时，状态能立即正确显示
    useLayoutEffect(() => {
        // 组件挂载时，先从 sessionStorage 恢复状态
        const cachedState = restoreStateFromCache();
        // 然后同步全局状态（确保一致性）
        const globalState = manager.getState();
        
        console.log('[useAudioPlayer] 组件挂载，恢复状态:', {
            song: song?.title,
            songId: song?.song_id,
            songFileUrl: song?.file_url,
            cachedSongId: cachedState?.currentSong?.song_id,
            cachedIsPlaying: cachedState?.isPlaying,
            cachedCurrentTime: cachedState?.currentTime,
            globalSongId: globalState.currentSong?.song_id,
            globalIsPlaying: globalState.isPlaying,
            globalCurrentTime: globalState.currentTime
        });
        
        // 合并状态：优先使用全局状态（更准确），但保留缓存的关键信息
        // 关键修复：即使 globalState.currentSong 存在，也要检查缓存中的 isPlaying 和 currentTime
        // 因为 pause 事件可能在页面切换时触发，导致 globalState.isPlaying 被错误重置为 false
        let finalState;
        if (globalState.currentSong) {
            // 全局状态有当前歌曲，但需要检查缓存中的播放状态和进度
            // 如果缓存中的状态与 globalState 不一致，优先使用缓存的状态（页面切换前的真实状态）
            if (cachedState?.currentSong && 
                cachedState.currentSong.song_id === globalState.currentSong.song_id) {
                // 缓存中的歌曲匹配，检查状态是否一致
                const cacheIsPlaying = cachedState.isPlaying;
                const cacheCurrentTime = cachedState.currentTime;
                const globalIsPlaying = globalState.isPlaying;
                const globalCurrentTime = globalState.currentTime;
                
                // 如果缓存中是播放状态，但 globalState 是暂停状态，说明可能是页面切换导致的 pause 事件
                // 优先使用缓存的状态（页面切换前的真实状态）
                if (cacheIsPlaying && !globalIsPlaying) {
                    console.log('[useAudioPlayer] 检测到状态不一致：缓存中是播放，globalState 是暂停，使用缓存状态');
                    // 同步更新 manager 的状态，确保后续监听器正确工作
                    manager.isPlaying = cacheIsPlaying;
                    manager.currentTime = cacheCurrentTime;
                    if (cachedState.duration) {
                        manager.duration = cachedState.duration;
                    }
                    
                    finalState = {
                        ...globalState,
                        isPlaying: cacheIsPlaying,
                        currentTime: cacheCurrentTime,
                        duration: cachedState.duration || globalState.duration
                    };
                } else {
                    // 状态一致，使用全局状态
                    finalState = globalState;
                }
                console.log('[useAudioPlayer] 使用全局状态（已检查缓存）');
            } else {
                // 没有匹配的缓存，使用全局状态
                finalState = globalState;
                console.log('[useAudioPlayer] 使用全局状态');
            }
        } else if (cachedState?.currentSong) {
            // 全局状态没有当前歌曲，但缓存中有，使用缓存的状态
            finalState = {
                ...globalState,
                currentSong: cachedState.currentSong,
                isPlaying: cachedState.isPlaying,
                currentTime: cachedState.currentTime,
                duration: cachedState.duration || globalState.duration
            };
            console.log('[useAudioPlayer] 使用缓存状态');
        } else {
            // 都没有，使用全局状态
            finalState = globalState;
            console.log('[useAudioPlayer] 使用默认全局状态');
        }
        
        // 如果传入的 song 存在，检查是否匹配当前播放的歌曲
        // 如果匹配，确保状态正确同步（特别是 currentTime）
        if (song && finalState.currentSong) {
            const songMatches = (song.song_id && finalState.currentSong.song_id && 
                song.song_id === finalState.currentSong.song_id) ||
                (song.file_url && finalState.currentSong.file_url && 
                isSameUrl(song.file_url, finalState.currentSong.file_url));
            
            if (songMatches) {
                console.log('[useAudioPlayer] 歌曲匹配，确保状态同步');
                // 如果 Audio 元素已加载，同步 currentTime
                if (manager.audioElement && manager.audioElement.readyState >= 2) {
                    // 确保 Audio 元素的 currentTime 和全局状态一致
                    if (Math.abs(manager.audioElement.currentTime - finalState.currentTime) > 0.5) {
                        manager.audioElement.currentTime = finalState.currentTime;
                        console.log('[useAudioPlayer] 同步 Audio 元素的 currentTime:', finalState.currentTime);
                    }
                }
            }
        }
        
        console.log('[useAudioPlayer] 最终状态:', {
            currentSongId: finalState.currentSong?.song_id,
            isPlaying: finalState.isPlaying,
            currentTime: finalState.currentTime
        });
        
        setState(finalState);
    }, []); // 只在组件挂载时执行一次，song 变化时通过 useEffect 处理

    // 注册状态监听器（在 useLayoutEffect 之后执行）
    useEffect(() => {
        const listener = (newState) => {
            setState(newState);
        };
        listenerRef.current = listener;
        
        // 注册监听器（不立即通知，因为 useLayoutEffect 已经同步了状态）
        manager.addListener(listener, false);
        
        return () => {
            // 清理时移除监听器
            if (listenerRef.current) {
                manager.removeListener(listenerRef.current);
                listenerRef.current = null;
            }
        };
    }, []);

    // 当 song 变化时，确保状态同步（特别是当 song 从 undefined 变成有值时）
    useEffect(() => {
        if (song) {
            const globalState = manager.getState();
            // 如果全局状态中有当前歌曲，且和传入的 song 匹配，确保状态同步
            if (globalState.currentSong) {
                const songMatches = (song.song_id && globalState.currentSong.song_id && 
                    song.song_id === globalState.currentSong.song_id) ||
                    (song.file_url && globalState.currentSong.file_url && 
                    isSameUrl(song.file_url, globalState.currentSong.file_url));
                
                if (songMatches) {
                    console.log('[useAudioPlayer] song 变化且匹配，同步状态');
                    // 确保本地状态和全局状态一致
                    setState(globalState);
                }
            }
        }
    }, [song?.song_id, song?.file_url]);

    // 当歌曲改变时，更新全局状态
    // 注意：只有在歌曲真正改变时才更新，避免不必要的重置
    // 这里只设置歌曲，不自动播放（等待用户点击播放按钮）
    useEffect(() => {
        if (song) {
            // 从全局管理器获取当前歌曲（而不是本地state），确保准确性
            const globalState = manager.getState();
            const currentSong = globalState.currentSong;
            
            // 检查是否是同一首歌：优先比较 song_id，如果没有则比较 file_url
            const isSameSong = currentSong && (
                (song.song_id && currentSong.song_id && song.song_id === currentSong.song_id) ||
                (song.file_url && currentSong.file_url && isSameUrl(song.file_url, currentSong.file_url))
            );
            
            // 只有当歌曲真正改变时才调用 setSong（不自动播放）
            // 如果歌曲相同，不应该调用 setSong，避免重置播放进度和状态
            if (!isSameSong) {
                console.log('[useAudioPlayer] 歌曲改变，设置新歌曲:', {
                    oldSongId: currentSong?.song_id,
                    newSongId: song.song_id
                });
                manager.setSong(song, false); // 明确不自动播放，等待用户操作
            } else {
                console.log('[useAudioPlayer] 歌曲相同，保持当前状态');
            }
            // 如果歌曲相同，不调用 setSong，保持当前播放状态和进度
        }
    }, [song?.song_id, song?.file_url]);

    // 播放/暂停
    const togglePlay = useCallback(async () => {
        // 如果切换的是不同的歌曲，先设置歌曲（自动播放如果之前正在播放）
        if (song && (!stateRef.current.currentSong || 
            !isSameUrl(stateRef.current.currentSong.file_url, song.file_url))) {
            // 检查之前是否正在播放
            const wasPlaying = stateRef.current.isPlaying;
            // 设置新歌曲，如果之前正在播放则自动播放
            manager.setSong(song, wasPlaying);
            // 如果之前没有播放，调用 togglePlay 开始播放
            if (!wasPlaying) {
                await manager.togglePlay();
            }
            // 如果之前正在播放，setSong 会自动调用 loadAndPlayNewSong，不需要再次调用 togglePlay
        } else {
            // 同一首歌，直接切换播放/暂停
            await manager.togglePlay();
        }
    }, [song]);

    // 设置播放位置
    const seekTo = useCallback((time) => {
        manager.seekTo(time);
    }, []);

    // 设置音量（全局统一）
    const setVolume = useCallback((volume) => {
        manager.setVolume(volume);
    }, []);

    // 设置播放速度（全局统一）
    const setPlaybackRate = useCallback((rate) => {
        manager.setPlaybackRate(rate);
    }, []);

    // 切换循环播放（全局统一）
    const toggleLoop = useCallback(() => {
        manager.toggleLoop();
    }, []);

    // 检查当前歌曲是否匹配（使用 useMemo 优化，确保在状态更新时重新计算）
    // 注意：依赖项包括 state，确保 state 变化时重新计算
    const isCurrentSong = useMemo(() => {
        // 如果 song 不存在，肯定不是当前歌曲
        if (!song) {
            console.log('[useAudioPlayer] isCurrentSong: song 不存在');
            return false;
        }
        
        // 如果全局状态中没有当前歌曲，肯定不是当前歌曲
        if (!state.currentSong) {
            console.log('[useAudioPlayer] isCurrentSong: state.currentSong 不存在');
            return false;
        }
        
        // 优先比较 song_id（最可靠）
        if (song.song_id && state.currentSong.song_id) {
            const matchById = song.song_id === state.currentSong.song_id;
            console.log('[useAudioPlayer] isCurrentSong 判断（by song_id):', {
                songId: song.song_id,
                stateSongId: state.currentSong.song_id,
                match: matchById
            });
            return matchById;
        }
        
        // 如果没有 song_id，比较 file_url
        if (song.file_url && state.currentSong.file_url) {
            const matchByUrl = isSameUrl(song.file_url, state.currentSong.file_url);
            console.log('[useAudioPlayer] isCurrentSong 判断（by file_url):', {
                songFileUrl: song.file_url,
                stateFileUrl: state.currentSong.file_url,
                match: matchByUrl
            });
            return matchByUrl;
        }
        
        // 都不匹配
        console.log('[useAudioPlayer] isCurrentSong 判断: 不匹配', {
            songId: song.song_id,
            songFileUrl: song.file_url,
            stateSongId: state.currentSong.song_id,
            stateFileUrl: state.currentSong.file_url
        });
        return false;
    }, [song, state]); // 依赖整个 song 和 state 对象，确保任何变化都能触发重新计算

    // 计算返回的值
    const returnIsPlaying = isCurrentSong ? state.isPlaying : false;
    const returnCurrentTime = isCurrentSong ? state.currentTime : 0;
    const returnDuration = isCurrentSong ? state.duration : (song?.duration || 0);
    
    // 调试日志：每次返回时记录
    console.log('[useAudioPlayer] 返回值:', {
        songId: song?.song_id,
        isCurrentSong,
        stateIsPlaying: state.isPlaying,
        stateCurrentTime: state.currentTime,
        returnIsPlaying,
        returnCurrentTime,
        returnDuration
    });
    
    return {
        // 播放状态（只有当前播放的歌曲才显示）
        isPlaying: returnIsPlaying,
        currentTime: returnCurrentTime,
        duration: returnDuration,
        
        // 全局统一的设置（所有播放器共享）
        volume: state.volume,
        playbackRate: state.playbackRate,
        loop: state.loop,
        
        // 标识
        isCurrentSong,
        
        // 操作方法
        togglePlay,
        seekTo,
        setVolume,
        setPlaybackRate,
        toggleLoop,
        audioRef: { current: manager.audioElement }
    };
}
