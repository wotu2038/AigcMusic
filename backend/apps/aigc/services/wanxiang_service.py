"""
阿里万相（通义万相）服务
使用阿里云DashScope SDK
"""
import json
import logging
import requests
import time
from django.conf import settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 尝试导入dashscope SDK
try:
    import dashscope
    from dashscope import ImageSynthesis, Generation, VideoSynthesis, Files
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger.warning('DashScope SDK未安装，请运行: pip install dashscope')


class WanxiangService:
    """阿里万相服务类"""
    
    def __init__(self):
        self.api_key = settings.ALIBABA_WANXIANG_API_KEY
        self.model_image = getattr(settings, 'ALIBABA_WANXIANG_MODEL_IMAGE', 'wanx-v1')
        self.model_text = getattr(settings, 'ALIBABA_WANXIANG_MODEL_TEXT', 'qwen-turbo')
        self.model_video = getattr(settings, 'ALIBABA_WANXIANG_MODEL_VIDEO', '')
        self.endpoint = getattr(settings, 'ALIBABA_WANXIANG_ENDPOINT', 'dashscope.aliyuncs.com')
        
        if not self.api_key:
            logger.warning('阿里万相API密钥未配置')
        
        # 初始化DashScope SDK
        if DASHSCOPE_AVAILABLE and self.api_key:
            dashscope.api_key = self.api_key
            dashscope.base_url = f"https://{self.endpoint}/api/v1"
    
    def generate_image(self, prompt: str, style: str = 'beautiful', count: int = 1) -> List[Dict]:
        """
        生成图片（使用DashScope SDK）
        
        Args:
            prompt: 图片描述提示词
            style: 图片风格（beautiful, abstract, realistic, minimalist, artistic）
            count: 生成数量（1-3）
        
        Returns:
            List[Dict]: 生成的图片信息列表，每个包含url和metadata
        """
        if not self.api_key:
            raise ValueError('阿里万相API密钥未配置')
        
        if not DASHSCOPE_AVAILABLE:
            raise ValueError('DashScope SDK未安装，请运行: pip install dashscope')
        
        # 构建完整的prompt
        style_map = {
            'beautiful': '唯美风格',
            'abstract': '抽象风格',
            'realistic': '写实风格',
            'minimalist': '简约风格',
            'artistic': '艺术风格'
        }
        style_text = style_map.get(style, '唯美风格')
        full_prompt = f'{prompt}，{style_text}，高质量，精美'
        
        try:
            # 使用DashScope SDK调用图片生成API
            rsp = ImageSynthesis.call(
                model=self.model_image,
                prompt=full_prompt,
                n=min(count, 3),  # 最多3张
                size='1024*1024',
                quality='standard'
            )
            
            if rsp.status_code == 200:
                images = []
                if rsp.output and rsp.output.results:
                    for idx, item in enumerate(rsp.output.results):
                        if item.url:
                            images.append({
                                'url': item.url,
                                'metadata': {
                                    'style': style,
                                    'prompt': full_prompt,
                                    'index': idx
                                }
                            })
                
                if not images:
                    raise Exception('API返回成功但未生成图片')
                
                logger.info(f'阿里万相图片生成成功，返回 {len(images)} 张图片')
                return images
            else:
                error_msg = rsp.message if hasattr(rsp, 'message') else '未知错误'
                logger.error(f'阿里万相图片生成失败: {error_msg}, Request ID: {rsp.request_id if hasattr(rsp, "request_id") else "N/A"}')
                raise Exception(f'图片生成失败: {error_msg}')
        
        except Exception as e:
            logger.error(f'阿里万相图片生成异常: {str(e)}', exc_info=True)
            raise Exception(f'图片生成失败: {str(e)}')
    
    def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """
        生成文字内容（使用DashScope SDK）
        
        Args:
            prompt: 文字生成提示词
            max_tokens: 最大token数
        
        Returns:
            str: 生成的文字内容
        """
        if not self.api_key:
            raise ValueError('阿里万相API密钥未配置')
        
        if not DASHSCOPE_AVAILABLE:
            raise ValueError('DashScope SDK未安装，请运行: pip install dashscope')
        
        try:
            # 使用DashScope SDK调用文字生成API（通义千问）
            from dashscope import Generation
            
            messages = [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            rsp = Generation.call(
                model=self.model_text,
                messages=messages,
                result_format='message',
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if rsp.status_code == 200:
                if 'output' in rsp and 'choices' in rsp.output:
                    return rsp.output.choices[0].message.content
                elif 'output' in rsp and 'text' in rsp.output:
                    return rsp.output.text
                else:
                    raise Exception('API返回格式异常')
            else:
                error_msg = rsp.message if hasattr(rsp, 'message') else '未知错误'
                logger.error(f'阿里万相文字生成失败: {error_msg}')
                raise Exception(f'文字生成失败: {error_msg}')
        
        except Exception as e:
            logger.error(f'阿里万相文字生成异常: {str(e)}', exc_info=True)
            raise Exception(f'文字生成失败: {str(e)}')
    
    def upload_image_to_dashscope(self, image_url: str) -> str:
        """
        将图片上传到DashScope Files服务，返回DashScope文件URL
        
        Args:
            image_url: 原始图片URL
        
        Returns:
            str: DashScope Files服务返回的文件ID（格式：fileid://xxx）或原始URL
        """
        try:
            import tempfile
            import os
            
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', mode='wb') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            try:
                # 上传到DashScope Files服务
                # purpose='file-extract' 用于文件提取，也可以尝试其他purpose
                upload_rsp = Files.upload(file_path=tmp_path, purpose='file-extract')
                
                if upload_rsp.status_code == 200 and upload_rsp.output:
                    # 提取file_id（output结构：{'uploaded_files': [{'file_id': '...'}]}）
                    uploaded_files = getattr(upload_rsp.output, 'uploaded_files', None)
                    if uploaded_files and len(uploaded_files) > 0:
                        file_id = uploaded_files[0].get('file_id') if isinstance(uploaded_files[0], dict) else getattr(uploaded_files[0], 'file_id', None)
                        if file_id:
                            # 使用fileid://格式
                            dashscope_url = f'fileid://{file_id}'
                            logger.info(f'图片已上传到DashScope Files，file_id: {file_id}')
                            return dashscope_url
                    
                    # 如果没有file_id，尝试其他格式
                    file_id = getattr(upload_rsp.output, 'file_id', None)
                    if file_id:
                        dashscope_url = f'fileid://{file_id}'
                        logger.info(f'图片已上传到DashScope Files，file_id: {file_id}')
                        return dashscope_url
                
                error_msg = upload_rsp.message if hasattr(upload_rsp, 'message') else '未知错误'
                logger.warning(f'上传图片到DashScope Files失败，未获取到file_id: {error_msg}')
                return image_url
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f'上传图片到DashScope Files失败，使用原始URL: {str(e)}')
            return image_url
    
    def generate_text_to_video(self, prompt: str, duration: int = 5, resolution: str = '720p') -> Dict:
        """
        文生视频（直接基于文本提示词生成视频，不需要图片）
        
        Args:
            prompt: 视频描述提示词
            duration: 视频时长（秒，通常5-10秒）
            resolution: 视频分辨率（480p, 720p, 1080p）
        
        Returns:
            Dict: 生成的视频信息，包含url和metadata
        """
        if not self.api_key:
            raise ValueError('阿里万相API密钥未配置')
        
        if not DASHSCOPE_AVAILABLE:
            raise ValueError('DashScope SDK未安装，请运行: pip install dashscope')
        
        if not self.model_video:
            raise ValueError('视频生成模型未配置，请在.env中设置ALIBABA_WANXIANG_MODEL_VIDEO')
        
        try:
            # 解析分辨率到尺寸
            resolution_map = {
                '480p': '480*480',
                '720p': '720*720',
                '1080p': '1080*1080'
            }
            size = resolution_map.get(resolution, '720*720')
            
            # 使用DashScope SDK调用视频生成API（文生视频）
            # 只需要prompt参数，不需要img_url
            logger.info(f'调用文生视频API，模型: {self.model_video}, 提示词: {prompt[:50]}...')
            rsp = VideoSynthesis.call(
                model=self.model_video,
                prompt=prompt,  # 只使用prompt参数（文生视频）
                duration=duration,
                size=size
            )
            
            # 视频生成是异步的，需要检查任务状态
            if rsp.status_code == 200:
                # 检查是否有task_id（异步任务）
                if hasattr(rsp.output, 'task_id') and rsp.output.task_id:
                    # 异步任务，需要轮询获取结果
                    task_id = rsp.output.task_id
                    logger.info(f'文生视频任务已创建，Task ID: {task_id}，开始轮询结果...')
                    
                    # 轮询获取结果（最多等待5分钟）
                    max_wait_time = 300  # 5分钟
                    start_time = time.time()
                    poll_interval = 5  # 每5秒轮询一次
                    
                    while time.time() - start_time < max_wait_time:
                        time.sleep(poll_interval)
                        status_rsp = VideoSynthesis.call(
                            model=self.model_video,
                            task=task_id
                        )
                        
                        if status_rsp.status_code == 200:
                            if hasattr(status_rsp.output, 'video_url') and status_rsp.output.video_url:
                                video_info = {
                                    'url': status_rsp.output.video_url,
                                    'metadata': {
                                        'prompt': prompt,
                                        'duration': duration,
                                        'resolution': resolution,
                                        'task_id': task_id
                                    }
                                }
                                logger.info(f'阿里万相文生视频成功，视频URL: {status_rsp.output.video_url}')
                                return video_info
                            elif hasattr(status_rsp.output, 'status'):
                                status = status_rsp.output.status
                                if status == 'FAILED':
                                    error_msg = getattr(status_rsp.output, 'message', '视频生成失败')
                                    raise Exception(f'视频生成失败: {error_msg}')
                                elif status == 'SUCCEEDED':
                                    # 理论上这里应该有video_url，如果没有则报错
                                    raise Exception('视频生成任务成功但未返回视频URL')
                                else:
                                    logger.info(f'文生视频任务 {task_id} 状态: {status}')
                        else:
                            error_msg = status_rsp.message if hasattr(status_rsp, 'message') else '未知错误'
                            logger.error(f'轮询文生视频任务 {task_id} 失败: {error_msg}')
                            raise Exception(f'视频生成失败: {error_msg}')
                    
                    raise Exception(f'文生视频任务超时（{max_wait_time}秒）')
                
                elif hasattr(rsp.output, 'video_url') and rsp.output.video_url:
                    # 同步任务（如果API支持）
                    video_info = {
                        'url': rsp.output.video_url,
                        'metadata': {
                            'prompt': prompt,
                            'duration': duration,
                            'resolution': resolution,
                            'task_id': rsp.output.task_id if hasattr(rsp.output, 'task_id') else None
                        }
                    }
                    logger.info(f'阿里万相文生视频成功（同步），视频URL: {rsp.output.video_url}')
                    return video_info
                else:
                    raise Exception('API返回成功但未生成视频URL或任务ID')
            else:
                error_msg = rsp.message if hasattr(rsp, 'message') else '未知错误'
                logger.error(f'阿里万相文生视频失败: {error_msg}, Request ID: {rsp.request_id if hasattr(rsp, "request_id") else "N/A"}')
                raise Exception(f'文生视频失败: {error_msg}')
        
        except Exception as e:
            logger.error(f'阿里万相文生视频异常: {str(e)}', exc_info=True)
            raise Exception(f'文生视频失败: {str(e)}')
    
    def generate_video(self, image_url: str, prompt: str, duration: int = 5, resolution: str = '720p') -> Dict:
        """
        生成视频（图生视频，基于首帧图片）
        
        Args:
            image_url: 首帧图片URL（歌词配图）
            prompt: 视频描述提示词
            duration: 视频时长（秒，通常5-10秒）
            resolution: 视频分辨率（480p, 720p, 1080p）
        
        Returns:
            Dict: 生成的视频信息，包含url和metadata
        """
        if not self.api_key:
            raise ValueError('阿里万相API密钥未配置')
        
        if not DASHSCOPE_AVAILABLE:
            raise ValueError('DashScope SDK未安装，请运行: pip install dashscope')
        
        if not self.model_video:
            raise ValueError('视频生成模型未配置，请在.env中设置ALIBABA_WANXIANG_MODEL_VIDEO')
        
        try:
            # 先尝试上传图片到DashScope Files服务（wan2.2-i2v-flash可能需要）
            logger.info(f'上传图片到DashScope Files: {image_url[:50]}...')
            dashscope_image_url = self.upload_image_to_dashscope(image_url)
            
            # 如果上传成功返回了fileid://格式，使用DashScope URL
            # 否则使用原始URL（但确保endpoint正确）
            if dashscope_image_url.startswith('fileid://'):
                final_image_url = dashscope_image_url
                logger.info(f'使用DashScope Files URL: {final_image_url}')
            else:
                # 确保URL使用正确的endpoint
                # 从Django配置中获取OSS endpoint，而不是硬编码
                from django.conf import settings
                configured_endpoint = settings.OSS_ENDPOINT.replace('https://', '').replace('http://', '').strip('/')
                if 'oss-rg-china-mainland' in dashscope_image_url:
                    # 如果配置的endpoint包含区域信息，使用它；否则使用默认的北京区域
                    if 'oss-cn-' in configured_endpoint:
                        # 从配置的endpoint提取区域信息
                        region_match = configured_endpoint.split('oss-cn-')[1].split('.')[0] if 'oss-cn-' in configured_endpoint else 'beijing'
                        target_endpoint = f'oss-cn-{region_match}'
                    else:
                        # 如果配置的endpoint不是区域endpoint，默认使用北京区域
                        target_endpoint = 'oss-cn-beijing'
                    dashscope_image_url = dashscope_image_url.replace('oss-rg-china-mainland', target_endpoint)
                    logger.info(f'已修正URL endpoint: {dashscope_image_url[:50]}...')
                final_image_url = dashscope_image_url
            
            # 解析分辨率到尺寸
            resolution_map = {
                '480p': '480*480',
                '720p': '720*720',
                '1080p': '1080*1080'
            }
            size = resolution_map.get(resolution, '720*720')
            
            # 使用DashScope SDK调用视频生成API（图生视频）
            # 根据官方API文档，使用input参数结构
            logger.info(f'调用视频生成API，模型: {self.model_video}, 图片URL: {final_image_url[:50]}...')
            
            # 解析分辨率格式（API需要480P格式，不是480p）
            resolution_map = {
                '480p': '480P',
                '720p': '720P',
                '1080p': '1080P'
            }
            resolution_param = resolution_map.get(resolution, '720P')
            
            # 使用extra_input传递parameters（根据DashScope SDK文档）
            rsp = VideoSynthesis.call(
                model=self.model_video,
                img_url=final_image_url,  # 使用DashScope Files URL或修正后的OSS URL
                prompt=prompt,
                duration=duration,
                size=size,
                extra_input={
                    'resolution': resolution_param,
                    'prompt_extend': True  # 启用提示词扩展
                }
            )
            
            # 视频生成可能是同步或异步的，需要检查返回结果
            if rsp.status_code == 200:
                # 先检查是否有video_url（同步返回）
                video_url = None
                task_id = None
                
                if hasattr(rsp.output, 'video_url') and rsp.output.video_url:
                    video_url = rsp.output.video_url
                    logger.info(f'视频生成成功（同步），视频URL: {video_url[:50]}...')
                elif isinstance(rsp.output, dict) and rsp.output.get('video_url'):
                    video_url = rsp.output.get('video_url')
                    logger.info(f'视频生成成功（同步），视频URL: {video_url[:50]}...')
                
                # 检查是否有task_id（异步任务）
                if not video_url:
                    if hasattr(rsp.output, 'task_id') and rsp.output.task_id:
                        task_id = rsp.output.task_id
                    elif isinstance(rsp.output, dict) and rsp.output.get('task_id'):
                        task_id = rsp.output.get('task_id')
                    
                    if task_id:
                        logger.info(f'视频生成任务已创建（异步），Task ID: {task_id}，开始轮询结果...')
                        
                        # 轮询获取结果（最多等待5分钟）
                        max_wait_time = 300  # 5分钟
                        start_time = time.time()
                        poll_interval = 5  # 每5秒轮询一次
                        
                        while time.time() - start_time < max_wait_time:
                            time.sleep(poll_interval)
                            status_rsp = VideoSynthesis.call(
                                model=self.model_video,
                                task=task_id
                            )
                            
                            if status_rsp.status_code == 200:
                                # 检查返回的video_url
                                if hasattr(status_rsp.output, 'video_url') and status_rsp.output.video_url:
                                    video_url = status_rsp.output.video_url
                                    break
                                elif isinstance(status_rsp.output, dict) and status_rsp.output.get('video_url'):
                                    video_url = status_rsp.output.get('video_url')
                                    break
                                elif hasattr(status_rsp.output, 'task_status'):
                                    task_status = status_rsp.output.task_status
                                    if task_status == 'FAILED':
                                        error_msg = getattr(status_rsp.output, 'message', '视频生成失败')
                                        raise Exception(f'视频生成失败: {error_msg}')
                                    elif task_status == 'SUCCEEDED':
                                        # 成功但可能video_url在output中
                                        if hasattr(status_rsp.output, 'video_url') and status_rsp.output.video_url:
                                            video_url = status_rsp.output.video_url
                                            break
                                        elif isinstance(status_rsp.output, dict) and status_rsp.output.get('video_url'):
                                            video_url = status_rsp.output.get('video_url')
                                            break
                                    logger.debug(f'视频生成中，状态: {task_status}')
                            else:
                                error_msg = status_rsp.message if hasattr(status_rsp, 'message') else '未知错误'
                                logger.error(f'查询视频生成状态失败: {error_msg}')
                                raise Exception(f'查询视频生成状态失败: {error_msg}')
                        
                        if not video_url:
                            raise Exception('视频生成超时，请稍后查询任务状态')
                
                # 返回视频信息
                if video_url:
                    video_info = {
                        'url': video_url,
                        'metadata': {
                            'prompt': prompt,
                            'duration': duration,
                            'resolution': resolution,
                            'task_id': task_id if task_id else None
                        }
                    }
                    logger.info(f'阿里万相视频生成成功，视频URL: {video_url[:50]}...')
                    return video_info
                else:
                    raise Exception('API返回成功但未生成视频URL或任务ID')
            else:
                error_msg = rsp.message if hasattr(rsp, 'message') else '未知错误'
                logger.error(f'阿里万相视频生成失败: {error_msg}, Request ID: {rsp.request_id if hasattr(rsp, "request_id") else "N/A"}')
                raise Exception(f'视频生成失败: {error_msg}')
        
        except Exception as e:
            logger.error(f'阿里万相视频生成异常: {str(e)}', exc_info=True)
            raise Exception(f'视频生成失败: {str(e)}')


# 创建全局服务实例
wanxiang_service = WanxiangService()

