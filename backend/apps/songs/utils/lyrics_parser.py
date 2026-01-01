"""
歌词文件解析工具
支持 LRC 和 SRT 格式
"""
import re
import logging

logger = logging.getLogger(__name__)


def parse_lrc_time_tag(time_tag):
    """
    解析 LRC 时间标签
    支持格式：[mm:ss.xx] 或 [mm:ss:xx] 或 [mm:ss]
    """
    # 移除方括号
    time_str = time_tag.replace('[', '').replace(']', '')
    
    # 匹配 [mm:ss.xx] 或 [mm:ss:xx] 格式
    match = re.match(r'^(\d{2}):(\d{2})[\.:](\d{2})$', time_str)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        centiseconds = int(match.group(3))
        return minutes * 60 + seconds + centiseconds / 100
    
    # 匹配 [mm:ss] 格式（无毫秒）
    match2 = re.match(r'^(\d{2}):(\d{2})$', time_str)
    if match2:
        minutes = int(match2.group(1))
        seconds = int(match2.group(2))
        return minutes * 60 + seconds
    
    return None


def parse_srt_time(time_str):
    """
    解析 SRT 时间格式
    格式：00:00:12,500 或 00:00:12.500
    """
    # 支持逗号和点作为毫秒分隔符
    time_str = time_str.replace(',', '.')
    
    # 匹配 HH:MM:SS.mmm 格式
    match = re.match(r'^(\d{2}):(\d{2}):(\d{2})\.(\d{3})$', time_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4))
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    
    return None


def is_lrc_format(content):
    """检测是否为 LRC 格式"""
    if not content or not isinstance(content, str):
        return False
    
    # 检测是否包含时间标签 [mm:ss.xx] 或 [mm:ss:xx] 或 [mm:ss]
    lrc_pattern = re.compile(r'\[\d{2}:\d{2}[\.:]?\d{0,2}\]')
    return bool(lrc_pattern.search(content))


def is_srt_format(content):
    """检测是否为 SRT 格式"""
    if not content or not isinstance(content, str):
        return False
    
    # 检测是否包含 SRT 格式特征：
    # 1. 序号行（纯数字）
    # 2. 时间行（HH:MM:SS,mmm --> HH:MM:SS,mmm）
    srt_pattern = re.compile(r'\d+\s+\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}')
    return bool(srt_pattern.search(content))


def parse_lrc(content):
    """
    解析 LRC 格式歌词
    返回格式：[{ time: number, text: string }, ...]
    """
    if not content:
        return []
    
    lines = content.split('\n')
    result = []
    
    for line in lines:
        trimmed_line = line.strip()
        if not trimmed_line:
            continue
        
        # 匹配所有时间标签和文本
        # 例如：[00:12.50]歌词内容 或 [00:12.50][00:15.30]歌词内容
        time_tag_pattern = re.compile(r'\[(\d{2}:\d{2}[\.:]?\d{0,2})\]')
        time_tags = []
        
        for match in time_tag_pattern.finditer(trimmed_line):
            time = parse_lrc_time_tag(match.group(0))
            if time is not None:
                time_tags.append(time)
        
        # 提取文本内容（移除所有时间标签）
        text = time_tag_pattern.sub('', trimmed_line).strip()
        
        if text:
            if time_tags:
                # 如果有多个时间标签，为每个时间创建一条记录
                for time in time_tags:
                    result.append({'time': time, 'text': text})
            # 没有时间标签的行（如元数据）跳过
    
    # 按时间排序
    result.sort(key=lambda x: x['time'])
    
    return result


def parse_srt(content):
    """
    解析 SRT 格式字幕/歌词
    返回格式：[{ start_time: number, end_time: number, text: string }, ...]
    注意：为了兼容LRC格式，我们使用start_time作为主要时间
    """
    if not content:
        return []
    
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行
        if not line:
            i += 1
            continue
        
        # 检查是否是序号行（纯数字）
        if line.isdigit():
            i += 1
            if i >= len(lines):
                break
            
            # 下一行应该是时间行
            time_line = lines[i].strip()
            i += 1
            
            # 解析时间行：HH:MM:SS,mmm --> HH:MM:SS,mmm
            time_match = re.match(
                r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})',
                time_line
            )
            
            if time_match:
                start_time = parse_srt_time(time_match.group(1))
                end_time = parse_srt_time(time_match.group(2))
                
                if start_time is not None and end_time is not None:
                    # 收集文本内容（可能有多行）
                    text_lines = []
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    text = '\n'.join(text_lines)
                    
                    if text:
                        # 使用start_time作为主要时间（兼容LRC格式）
                        result.append({
                            'time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
        else:
            i += 1
    
    # 按时间排序
    result.sort(key=lambda x: x['time'])
    
    return result


def parse_lyrics_file(file_content, filename=None):
    """
    解析歌词文件（自动检测格式）
    
    Args:
        file_content: 文件内容（字符串或字节）
        filename: 文件名（可选，用于格式判断）
    
    Returns:
        {
            'format': 'lrc' | 'srt' | 'plain',
            'content': str,  # 原始文本内容
            'parsed': list   # 解析后的数据
        }
    """
    # 如果是字节，转换为字符串
    if isinstance(file_content, bytes):
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('gbk')
            except UnicodeDecodeError:
                content = file_content.decode('utf-8', errors='ignore')
    else:
        content = file_content
    
    # 根据文件名或内容检测格式
    if filename:
        filename_lower = filename.lower()
        if filename_lower.endswith('.lrc'):
            format_type = 'lrc'
        elif filename_lower.endswith('.srt'):
            format_type = 'srt'
        else:
            # 根据内容自动检测
            if is_lrc_format(content):
                format_type = 'lrc'
            elif is_srt_format(content):
                format_type = 'srt'
            else:
                format_type = 'plain'
    else:
        # 根据内容自动检测
        if is_lrc_format(content):
            format_type = 'lrc'
        elif is_srt_format(content):
            format_type = 'srt'
        else:
            format_type = 'plain'
    
    # 解析内容
    if format_type == 'lrc':
        parsed = parse_lrc(content)
    elif format_type == 'srt':
        parsed = parse_srt(content)
    else:
        parsed = []
    
    return {
        'format': format_type,
        'content': content,
        'parsed': parsed
    }

