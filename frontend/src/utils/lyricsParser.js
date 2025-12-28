/**
 * 歌词解析工具
 * 支持 LRC 格式和纯文本格式
 */

/**
 * 解析 LRC 时间标签
 * 支持格式：[mm:ss.xx] 或 [mm:ss:xx]
 */
function parseLRCTimeTag(timeTag) {
    // 移除方括号
    const timeStr = timeTag.replace(/[\[\]]/g, '');
    
    // 匹配 [mm:ss.xx] 或 [mm:ss:xx] 格式
    const match = timeStr.match(/^(\d{2}):(\d{2})[\.:](\d{2})$/);
    if (match) {
        const minutes = parseInt(match[1], 10);
        const seconds = parseInt(match[2], 10);
        const centiseconds = parseInt(match[3], 10);
        return minutes * 60 + seconds + centiseconds / 100;
    }
    
    // 匹配 [mm:ss] 格式（无毫秒）
    const match2 = timeStr.match(/^(\d{2}):(\d{2})$/);
    if (match2) {
        const minutes = parseInt(match2[1], 10);
        const seconds = parseInt(match2[2], 10);
        return minutes * 60 + seconds;
    }
    
    return null;
}

/**
 * 检测是否为 LRC 格式
 */
function isLRCFormat(lyrics) {
    if (!lyrics || typeof lyrics !== 'string') return false;
    
    // 检测是否包含时间标签 [mm:ss.xx] 或 [mm:ss:xx] 或 [mm:ss]
    const lrcPattern = /\[\d{2}:\d{2}[\.:]?\d{0,2}\]/;
    return lrcPattern.test(lyrics);
}

/**
 * 解析 LRC 格式歌词
 * 返回格式：[{ time: number, text: string }, ...]
 */
function parseLRC(lyrics) {
    if (!lyrics) return [];
    
    const lines = lyrics.split('\n');
    const result = [];
    
    for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;
        
        // 匹配所有时间标签和文本
        // 例如：[00:12.50]歌词内容 或 [00:12.50][00:15.30]歌词内容
        const timeTagPattern = /\[(\d{2}:\d{2}[\.:]?\d{0,2})\]/g;
        const timeTags = [];
        let match;
        
        while ((match = timeTagPattern.exec(trimmedLine)) !== null) {
            const time = parseLRCTimeTag(match[0]);
            if (time !== null) {
                timeTags.push(time);
            }
        }
        
        // 提取文本内容（移除所有时间标签）
        const text = trimmedLine.replace(/\[\d{2}:\d{2}[\.:]?\d{0,2}\]/g, '').trim();
        
        if (text) {
            if (timeTags.length > 0) {
                // 如果有多个时间标签，为每个时间创建一条记录
                for (const time of timeTags) {
                    result.push({ time, text });
                }
            } else {
                // 没有时间标签，可能是元数据行（如 [ti:歌曲名]），跳过或处理
                // 这里我们跳过元数据行
            }
        }
    }
    
    // 按时间排序
    result.sort((a, b) => a.time - b.time);
    
    return result;
}

/**
 * 解析纯文本歌词
 * 返回格式：[{ time: null, text: string }, ...]
 */
function parsePlainText(lyrics) {
    if (!lyrics) return [];
    
    const lines = lyrics.split('\n');
    return lines
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(text => ({ time: null, text }));
}

/**
 * 解析歌词（自动检测格式）
 * 返回格式：
 * {
 *   type: 'lrc' | 'plain',
 *   lines: [{ time: number | null, text: string }, ...]
 * }
 */
export function parseLyrics(lyrics) {
    if (!lyrics || typeof lyrics !== 'string') {
        return {
            type: 'plain',
            lines: []
        };
    }
    
    if (isLRCFormat(lyrics)) {
        const lines = parseLRC(lyrics);
        return {
            type: 'lrc',
            lines
        };
    } else {
        const lines = parsePlainText(lyrics);
        return {
            type: 'plain',
            lines
        };
    }
}

/**
 * 根据当前播放时间找到对应的歌词行索引
 * @param {Array} lines - 歌词行数组 [{ time, text }, ...]
 * @param {number} currentTime - 当前播放时间（秒）
 * @returns {number} - 歌词行索引，-1 表示未找到
 */
export function findCurrentLyricIndex(lines, currentTime) {
    if (!lines || lines.length === 0) return -1;
    
    // 对于纯文本模式，返回 -1（不高亮）
    if (lines[0].time === null) return -1;
    
    // 二分查找当前时间对应的歌词行
    let left = 0;
    let right = lines.length - 1;
    let result = -1;
    
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const midTime = lines[mid].time;
        
        if (midTime <= currentTime) {
            result = mid;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return result;
}


