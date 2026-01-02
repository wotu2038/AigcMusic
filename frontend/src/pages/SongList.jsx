import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import AudioPlayer from '../components/AudioPlayer';
import './SongList.css';

// 模块级别的缓存，用于在组件重新挂载时保持状态
// 这样即使组件卸载，数据也不会丢失
let cachedSongs = [];
let cachedPage = 1;
let cachedKeyword = '';
let cachedTotalPages = 1;
let hasCachedData = false;

// 歌曲行组件（简洁版，只负责渲染）
function SongRow({ song }) {
    return (
        <tr>
            <td>{song.song_id}</td>
            <td>
                <Link to={`/songs/${song.song_id}`} className="song-link">
                    {song.title}
                </Link>
            </td>
            <td>{song.artist}</td>
            <td>{song.album}</td>
            <td>{song.formatted_duration}</td>
            <td>
                {song.cover_url && (
                    <img 
                        src={song.cover_url} 
                        alt={song.title}
                        className="song-cover-thumb"
                    />
                )}
            </td>
            <td>
                {song.file_url ? (
                    <AudioPlayer song={song} variant="inline" />
                ) : (
                    <span>加载中...</span>
                )}
            </td>
        </tr>
    );
}

// 后端现在直接返回完整数据，无需预加载函数

function SongList() {
    const navigate = useNavigate();
    // 从缓存恢复状态（如果存在）
    const [songs, setSongs] = useState(() => hasCachedData ? cachedSongs : []);
    const [loading, setLoading] = useState(() => !hasCachedData);
    const [error, setError] = useState('');
    // 分离输入关键词和搜索关键词
    const [inputKeyword, setInputKeyword] = useState(() => cachedKeyword); // 输入框的值（用于下拉菜单）
    const [searchKeyword, setSearchKeyword] = useState(() => cachedKeyword); // 实际用于搜索的关键词（只有点击搜索时才更新）
    const [page, setPage] = useState(() => cachedPage);
    const [totalPages, setTotalPages] = useState(() => cachedTotalPages);
    const [totalRecords, setTotalRecords] = useState(0);
    
    // 搜索下拉菜单相关状态
    const [suggestions, setSuggestions] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);
    
    // 用于跟踪当前添加的 preload link 元素，方便清理
    const preloadLinksRef = useRef([]);
    // 用于防抖的定时器
    const debounceTimerRef = useRef(null);
    // 用于点击外部关闭下拉菜单
    const searchFormRef = useRef(null);
    
    useEffect(() => {
        // 检查是否是首次加载，或者 page/searchKeyword 发生了变化
        const pageChanged = cachedPage !== page;
        const keywordChanged = cachedKeyword !== searchKeyword;
        
        // 只在首次加载或参数变化时加载数据
        if (!hasCachedData || pageChanged || keywordChanged) {
            loadSongs();
        } else {
            // 如果缓存存在且参数没变，直接使用缓存数据，不重新加载
            setLoading(false);
        }
    }, [page, searchKeyword]);
    
    // 使用 link rel="preload" 预加载所有歌曲的音频（方案2）
    // 当 songs 变化时自动预加载（包括换页、搜索）
    useEffect(() => {
        // 清理旧的 preload link
        preloadLinksRef.current.forEach(link => {
            if (link && link.parentNode) {
                link.parentNode.removeChild(link);
            }
        });
        preloadLinksRef.current = [];
        
        // 为每首歌曲添加 preload link
        if (songs.length > 0) {
            console.log('[SongList] 使用 link rel="preload" 预加载', songs.length, '首歌曲');
            songs.forEach((song, index) => {
                if (song.file_url) {
                    const link = document.createElement('link');
                    link.rel = 'preload';
                    link.as = 'audio';
                    link.href = song.file_url;
                    link.crossOrigin = 'anonymous';
                    // 添加唯一标识，方便调试
                    link.setAttribute('data-song-id', song.song_id || index);
                    document.head.appendChild(link);
                    preloadLinksRef.current.push(link);
                }
            });
        }
        
        // 组件卸载时清理所有 preload link
        return () => {
            preloadLinksRef.current.forEach(link => {
                if (link && link.parentNode) {
                    link.parentNode.removeChild(link);
                }
            });
            preloadLinksRef.current = [];
        };
    }, [songs]);
    
    const loadSongs = async () => {
        setLoading(true);
        setError('');
        
        try {
            const params = {
                page: page,
                limit: 10
            };
            
            if (searchKeyword) {
                params.keyword = searchKeyword;  // 后端API期望的参数名是 keyword
            }
            
            const response = await api.get('/songs/', { params });
            console.log('[SongList] API响应:', response.data);
            // 后端返回结构：{ success, message, data: { songs, pagination } }
            const data = response.data.data || response.data;
            const songsList = data.songs || data.results || [];
            console.log('[SongList] 解析后的歌曲列表:', songsList);
            
            // 后端现在直接返回包含 file_url 的完整数据，无需预加载
            // 更新状态
            setSongs(songsList);
            setTotalPages(data.pagination?.pages || 1);
            setTotalRecords(data.pagination?.total || 0);
            
            // 更新缓存
            cachedSongs = songsList;
            cachedPage = page;
            cachedKeyword = searchKeyword;
            cachedTotalPages = data.pagination?.pages || 1;
            hasCachedData = true;
        } catch (err) {
            console.error('[SongList] 加载歌曲列表失败:', err);
            console.error('[SongList] 错误详情:', {
                message: err.message,
                response: err.response,
                status: err.response?.status,
                data: err.response?.data
            });
            setError(err.response?.data?.message || err.message || '加载歌曲列表失败');
        } finally {
            setLoading(false);
        }
    };
    
    // 高亮关键词
    const highlightKeyword = (text, keyword) => {
        if (!keyword || !text || !keyword.trim()) return text;
        
        // 转义特殊字符
        const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedKeyword})`, 'gi');
        const parts = text.split(regex);
        
        return parts.map((part, index) => {
            if (regex.test(part)) {
                return <mark key={index} className="search-highlight">{part}</mark>;
            }
            return <span key={index}>{part}</span>;
        });
    };
    
    // 加载搜索建议（用于下拉菜单）
    const loadSuggestions = useCallback(async (searchKeyword) => {
        if (!searchKeyword || searchKeyword.trim().length === 0) {
            setSuggestions([]);
            setShowDropdown(false);
            return;
        }
        
        setLoadingSuggestions(true);
        try {
            const params = {
                keyword: searchKeyword.trim(),
                page: 1,
                limit: 10  // 最多返回10条
            };
            
            const response = await api.get('/songs/', { params });
            const data = response.data.data || response.data;
            const songsList = data.songs || data.results || [];
            
            // 限制显示10条
            setSuggestions(songsList.slice(0, 10));
            setShowDropdown(songsList.length > 0);
        } catch (err) {
            console.error('[SongList] 加载搜索建议失败:', err);
            setSuggestions([]);
            setShowDropdown(false);
        } finally {
            setLoadingSuggestions(false);
        }
    }, []);
    
    // 处理输入变化（带防抖）- 只更新输入框，不触发列表搜索
    const handleInputChange = (e) => {
        const value = e.target.value;
        setInputKeyword(value); // 只更新输入框的值，不更新搜索关键词
        
        // 清除之前的定时器
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }
        
        // 如果输入为空，立即关闭下拉菜单
        if (!value || value.trim().length === 0) {
            setSuggestions([]);
            setShowDropdown(false);
            setLoadingSuggestions(false);
            return;
        }
        
        // 设置防抖，300ms后执行搜索建议（只用于下拉菜单）
        debounceTimerRef.current = setTimeout(() => {
            loadSuggestions(value);
        }, 300);
    };
    
    // 处理点击下拉选项
    const handleSuggestionClick = (song) => {
        setShowDropdown(false);
        navigate(`/songs/${song.song_id}`);
    };
    
    // 处理搜索按钮点击或Enter键
    const handleSearch = (e) => {
        e.preventDefault();
        setShowDropdown(false);
        // 将输入框的关键词同步到搜索关键词，触发列表搜索
        setSearchKeyword(inputKeyword);
        setPage(1);
        // 搜索时清除缓存，强制重新加载
        hasCachedData = false;
        // loadSongs 会在 useEffect 中自动调用（因为 searchKeyword 变化了）
    };
    
    // 点击外部关闭下拉菜单
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchFormRef.current && !searchFormRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };
        
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);
    
    // 清理防抖定时器
    useEffect(() => {
        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, []);
    
    if (loading && songs.length === 0) {
        return <Loading text="加载歌曲列表..." />;
    }
    
    return (
        <div className="song-list-container">
            <div className="song-list-header">
                <h2>歌曲库</h2>
                <form onSubmit={handleSearch} className="search-form" ref={searchFormRef}>
                    <div className="search-input-wrapper">
                        <input
                            type="text"
                            value={inputKeyword}
                            onChange={handleInputChange}
                            onFocus={() => {
                                if (suggestions.length > 0) {
                                    setShowDropdown(true);
                                }
                            }}
                            placeholder="搜索歌曲/歌手/专辑"
                            className="search-input"
                        />
                        {showDropdown && inputKeyword && inputKeyword.trim() && (
                            <>
                                {loadingSuggestions ? (
                                    <div className="search-dropdown">
                                        <div className="search-dropdown-loading">搜索中...</div>
                                    </div>
                                ) : suggestions.length > 0 ? (
                                    <div className="search-dropdown">
                                        {suggestions.map((song) => (
                                            <div
                                                key={song.song_id}
                                                className="search-dropdown-item"
                                                onClick={() => handleSuggestionClick(song)}
                                            >
                                                <div className="search-dropdown-text">
                                                    {highlightKeyword(`${song.title} - ${song.artist}`, inputKeyword)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : null}
                            </>
                        )}
                    </div>
                    <button type="submit" className="btn">搜索</button>
                </form>
            </div>
            
            <ErrorMessage message={error} onClose={() => setError('')} />
            
            {songs.length > 0 ? (
                <>
                    <div className="song-list">
                        <table className="song-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>歌名</th>
                                    <th>歌手</th>
                                    <th>专辑</th>
                                    <th>时长</th>
                                    <th>封面</th>
                                    <th>播放</th>
                                </tr>
                            </thead>
                            <tbody>
                                {songs.map((song, index) => {
                                    if (!song) return null;
                                    
                                    return (
                                        <SongRow 
                                            key={song.song_id || `song-${index}`}
                                            song={song}
                                        />
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                    
                    {totalRecords > 0 && (
                        <div className="pagination">
                            <div className="pagination-info">
                                <span className="pagination-total">共 {totalRecords} 条记录</span>
                                {totalPages > 0 && (
                                    <span className="pagination-page">
                                        第 {page} 页 / 共 {totalPages} 页
                                    </span>
                                )}
                            </div>
                            {totalPages > 1 && (
                                <div className="pagination-controls">
                                    <button
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                        className="btn btn-secondary"
                                    >
                                        上一页
                                    </button>
                                    <button
                                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                        disabled={page === totalPages}
                                        className="btn btn-secondary"
                                    >
                                        下一页
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </>
            ) : (
                <div className="empty-state">
                    <p>暂无歌曲</p>
                </div>
            )}
        </div>
    );
}

export default SongList;

