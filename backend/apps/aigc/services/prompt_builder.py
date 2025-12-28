"""
Prompt构建器
用于构建各种AIGC任务的提示词
"""
from typing import List, Dict
from apps.comments.models import Comment


class PromptBuilder:
    """Prompt构建器"""
    
    @staticmethod
    def build_lyric_image_prompt(song_title: str, artist: str, lyrics: str, style: str = 'beautiful') -> str:
        """
        构建歌词配图的提示词
        
        Args:
            song_title: 歌曲标题
            artist: 艺术家
            lyrics: 歌词内容（关键段落）
            style: 图片风格
        
        Returns:
            str: 完整的提示词
        """
        # 提取歌词的关键部分（前200字或副歌部分）
        lyrics_key = lyrics[:200] if len(lyrics) > 200 else lyrics
        
        prompt = f"""为歌曲《{song_title}》创作配图。
艺术家：{artist}
歌词片段：{lyrics_key}

要求：
1. 体现歌词的意境和情感
2. 画面精美，富有艺术感
3. 适合作为音乐配图
4. 风格：{style}
"""
        return prompt.strip()
    
    @staticmethod
    def build_comment_summary_prompt(song_title: str, artist: str, comments: List[Comment]) -> str:
        """
        构建评论摘要的提示词
        
        Args:
            song_title: 歌曲标题
            artist: 艺术家
            comments: 评论列表
        
        Returns:
            str: 完整的提示词
        """
        # 提取评论内容（最多10条热门评论）
        comment_texts = []
        for comment in comments[:10]:
            comment_texts.append(f"- {comment.content}")
        
        comments_text = '\n'.join(comment_texts)
        
        prompt = f"""基于以下用户评论，为歌曲《{song_title}》（{artist}）生成一段评价摘要（100-200字）。

用户评论：
{comments_text}

要求：
1. 总结用户的整体评价和感受
2. 提取关键词和主题
3. 语言简洁、客观
4. 突出歌曲的特点和亮点
5. 字数控制在100-200字之间
"""
        return prompt.strip()
    
    @staticmethod
    def build_lyric_video_prompt(song_title: str, artist: str, lyrics: str, style: str = 'beautiful') -> str:
        """
        构建歌词视频的提示词
        
        Args:
            song_title: 歌曲标题
            artist: 艺术家
            lyrics: 歌词内容（关键段落）
            style: 视频风格
        
        Returns:
            str: 完整的提示词
        """
        lyrics_key = lyrics[:200] if len(lyrics) > 200 else lyrics
        
        style_map = {
            'beautiful': '唯美、流畅',
            'abstract': '抽象、艺术',
            'realistic': '写实、自然',
            'minimalist': '简约、优雅',
            'artistic': '艺术、创意'
        }
        style_text = style_map.get(style, '唯美、流畅')
        
        prompt = f"""基于这首歌曲《{song_title}》（{artist}）的配图，生成一段音乐视频。

歌词片段：{lyrics_key}

要求：
1. 视频要体现歌词的意境和情感
2. 画面流畅自然，富有动感
3. 风格：{style_text}
4. 适合作为音乐MV使用
5. 画面要有节奏感，与音乐节拍呼应
"""
        return prompt.strip()
    
    @staticmethod
    def build_text_to_video_prompt(song_title: str, artist: str, lyrics: str, style: str = 'beautiful', mood: str = '治愈') -> str:
        """
        构建文生视频的提示词（直接基于歌词生成视频，不需要图片）
        
        Args:
            song_title: 歌曲标题
            artist: 艺术家
            lyrics: 歌词内容
            style: 视频风格
            mood: 视频氛围
        
        Returns:
            str: 完整的提示词
        """
        # 提取歌词关键段落（用于视频生成）
        lyrics_key = PromptBuilder.extract_lyrics_key_section(lyrics, num_lines=10)
        
        style_map = {
            'beautiful': '唯美、流畅',
            'abstract': '抽象、艺术',
            'realistic': '写实、自然',
            'minimalist': '简约、优雅',
            'artistic': '艺术、创意'
        }
        style_text = style_map.get(style, '唯美、流畅')
        
        prompt = f"""为歌曲《{song_title}》（{artist}）生成一段音乐MV视频。

歌词内容：
{lyrics_key}

要求：
1. 视频要完美体现歌词的意境和情感
2. 画面流畅自然，富有动感和节奏感
3. 风格：{style_text}，氛围：{mood}
4. 适合作为音乐MV使用
5. 画面要有节奏感，与音乐节拍呼应
6. 色彩丰富，视觉冲击力强
7. 时长适中，适合循环播放
"""
        return prompt.strip()
    
    @staticmethod
    def extract_lyrics_key_section(lyrics: str, section_type: str = 'chorus', num_lines: int = 5) -> str:
        """
        提取歌词关键段落
        
        Args:
            lyrics: 完整歌词
            section_type: 段落类型（chorus: 副歌, verse: 主歌, all: 全部）
        
        Returns:
            str: 提取的歌词段落
        """
        if not lyrics:
            return ''
        
        # 简单的段落提取逻辑
        # 实际可以根据歌词格式（如标记了[副歌]）来提取
        lines = lyrics.split('\n')
        
        if section_type == 'chorus':
            # 尝试找到副歌部分（通常包含重复的段落）
            # 这里使用简单的启发式方法：找到最长的重复段落
            # 实际应用中可能需要更复杂的逻辑
            return '\n'.join(lines[:8])  # 返回前8行作为示例
        elif section_type == 'verse':
            return '\n'.join(lines[:4])  # 返回前4行
        else:
            return lyrics[:200]  # 返回前200字

