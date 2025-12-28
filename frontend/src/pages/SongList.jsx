import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
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
    // 从缓存恢复状态（如果存在）
    const [songs, setSongs] = useState(() => hasCachedData ? cachedSongs : []);
    const [loading, setLoading] = useState(() => !hasCachedData);
    const [error, setError] = useState('');
    const [keyword, setKeyword] = useState(() => cachedKeyword);
    const [page, setPage] = useState(() => cachedPage);
    const [totalPages, setTotalPages] = useState(() => cachedTotalPages);
    
    // 用于跟踪当前添加的 preload link 元素，方便清理
    const preloadLinksRef = useRef([]);
    
    useEffect(() => {
        // 检查是否是首次加载，或者 page/keyword 发生了变化
        const pageChanged = cachedPage !== page;
        const keywordChanged = cachedKeyword !== keyword;
        
        // 只在首次加载或参数变化时加载数据
        if (!hasCachedData || pageChanged || keywordChanged) {
            loadSongs();
        } else {
            // 如果缓存存在且参数没变，直接使用缓存数据，不重新加载
            setLoading(false);
        }
    }, [page, keyword]);
    
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
            
            if (keyword) {
                params.keyword = keyword;  // 后端API期望的参数名是 keyword
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
            
            // 更新缓存
            cachedSongs = songsList;
            cachedPage = page;
            cachedKeyword = keyword;
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
    
    const handleSearch = (e) => {
        e.preventDefault();
        setPage(1);
        // 搜索时清除缓存，强制重新加载
        hasCachedData = false;
        loadSongs();
    };
    
    if (loading && songs.length === 0) {
        return <Loading text="加载歌曲列表..." />;
    }
    
    return (
        <div className="song-list-container">
            <div className="song-list-header">
                <h2>歌曲库</h2>
                <form onSubmit={handleSearch} className="search-form">
                    <input
                        type="text"
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        placeholder="搜索歌曲/歌手/专辑"
                        className="search-input"
                    />
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
                    
                    {totalPages > 1 && (
                        <div className="pagination">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="btn btn-secondary"
                            >
                                上一页
                            </button>
                            <span className="pagination-info">
                                {page} / {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="btn btn-secondary"
                            >
                                下一页
                            </button>
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

