"""
阿里云OSS存储后端
"""
import os
import oss2
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.utils import timezone
from datetime import datetime


@deconstructible
class OSSStorage(Storage):
    """阿里云OSS存储类"""
    
    def __init__(self, access_key_id=None, access_key_secret=None, 
                 endpoint=None, bucket_name=None, base_path=''):
        self.access_key_id = access_key_id or settings.OSS_ACCESS_KEY_ID
        self.access_key_secret = access_key_secret or settings.OSS_ACCESS_KEY_SECRET
        self.endpoint = endpoint or settings.OSS_ENDPOINT
        self.bucket_name = bucket_name or settings.OSS_BUCKET_NAME
        self.base_path = base_path
        
        # 延迟初始化bucket，避免在导入时就需要配置
        self._bucket = None
    
    @property
    def bucket(self):
        """延迟初始化OSS bucket"""
        if self._bucket is None:
            import logging
            logger = logging.getLogger(__name__)
            
            # 初始化OSS客户端
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            
            # 处理endpoint格式
            # endpoint格式可能是: https://oss-rg-china-mainland.aliyuncs.com 或 https://oss-cn-beijing.aliyuncs.com
            # 需要提取域名部分，确保不包含协议前缀
            endpoint_clean = self.endpoint.replace('https://', '').replace('http://', '').strip('/')
            
            # 如果endpoint是跨区域endpoint（oss-rg-china-mainland），但bucket实际在某个区域
            # 需要根据bucket的实际位置使用正确的endpoint
            # 先尝试使用配置的endpoint，如果失败再尝试区域endpoint
            logger.info(f'初始化OSS Bucket: bucket={self.bucket_name}, endpoint={endpoint_clean}')
            
            # 创建Bucket对象，明确指定endpoint
            self._bucket = oss2.Bucket(auth, endpoint_clean, self.bucket_name)
            self._actual_endpoint = endpoint_clean  # 默认使用配置的endpoint
            
            # 测试连接并获取bucket信息
            try:
                bucket_info = self._bucket.get_bucket_info()
                logger.info(f'OSS Bucket连接成功: {self.bucket_name}, Location: {bucket_info.location}')
                
                # 如果bucket的Location与endpoint不匹配，需要重新初始化
                # 例如：bucket在oss-cn-beijing，但endpoint是oss-rg-china-mainland
                if bucket_info.location:
                    # bucket_info.location 格式可能是: oss-cn-beijing 或 cn-beijing
                    # 需要构建正确的endpoint: oss-cn-beijing.aliyuncs.com
                    if bucket_info.location.startswith('oss-'):
                        # 已经是完整格式: oss-cn-beijing
                        region_endpoint = f"{bucket_info.location}.aliyuncs.com"
                    else:
                        # 格式: cn-beijing，需要添加oss-前缀
                        region_endpoint = f"oss-{bucket_info.location}.aliyuncs.com"
                    
                    if endpoint_clean != region_endpoint and 'oss-rg-china-mainland' in endpoint_clean:
                        logger.warning(f'Endpoint不匹配，bucket Location: {bucket_info.location}, 当前endpoint: {endpoint_clean}, 切换到: {region_endpoint}')
                        # 重新创建bucket对象使用正确的endpoint
                        self._bucket = oss2.Bucket(auth, region_endpoint, self.bucket_name)
                        self._actual_endpoint = region_endpoint  # 保存实际使用的endpoint
                        logger.info(f'已切换到区域endpoint: {region_endpoint}')
                    else:
                        self._actual_endpoint = endpoint_clean  # 保存实际使用的endpoint
            except Exception as e:
                logger.error(f'OSS Bucket连接失败: {str(e)}')
                # 如果跨区域endpoint失败，尝试使用区域endpoint
                if 'oss-rg-china-mainland' in endpoint_clean:
                    logger.info('跨区域endpoint失败，尝试从配置的endpoint提取区域信息...')
                    # 尝试从配置的endpoint提取区域信息，而不是硬编码
                    # 如果配置的endpoint包含区域信息，使用它；否则使用默认的北京区域
                    if 'oss-cn-' in endpoint_clean:
                        # 从配置的endpoint提取区域信息（例如：oss-cn-beijing）
                        region_match = endpoint_clean.split('oss-cn-')[1].split('.')[0] if 'oss-cn-' in endpoint_clean else None
                        if region_match:
                            region_endpoint = f'oss-cn-{region_match}.aliyuncs.com'
                        else:
                            # 如果无法提取，使用配置的endpoint（去掉协议前缀）
                            region_endpoint = endpoint_clean
                    else:
                        # 如果配置的endpoint不是区域endpoint，尝试使用配置的endpoint本身
                        # 或者根据bucket_name推断（这里简化处理，使用配置的endpoint）
                        region_endpoint = endpoint_clean.replace('oss-rg-china-mainland', 'oss-cn-beijing')
                    logger.info(f'尝试使用区域endpoint: {region_endpoint}')
                    self._bucket = oss2.Bucket(auth, region_endpoint, self.bucket_name)
                    try:
                        bucket_info = self._bucket.get_bucket_info()
                        self._actual_endpoint = region_endpoint  # 保存实际使用的endpoint
                        logger.info(f'使用区域endpoint成功: {region_endpoint}, Location: {bucket_info.location}')
                    except Exception as e2:
                        logger.error(f'区域endpoint也失败: {str(e2)}')
                        raise
                else:
                    raise
        return self._bucket
    
    def _get_full_path(self, name):
        """获取完整路径"""
        if self.base_path:
            return f"{self.base_path}/{name}".lstrip('/')
        return name.lstrip('/')
    
    def _open(self, name, mode='rb'):
        """打开文件"""
        full_path = self._get_full_path(name)
        try:
            obj = self.bucket.get_object(full_path)
            return ContentFile(obj.read())
        except oss2.exceptions.NoSuchKey:
            raise FileNotFoundError(f"File {name} not found in OSS")
    
    def _save(self, name, content):
        """保存文件到OSS"""
        import logging
        import mimetypes
        logger = logging.getLogger(__name__)
        
        full_path = self._get_full_path(name)
        
        # 读取文件内容
        content.seek(0)
        file_content = content.read()
        file_size = len(file_content)
        
        # 根据文件扩展名设置Content-Type
        content_type, _ = mimetypes.guess_type(name)
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
            # 对于音频文件，设置Content-Disposition为inline，允许浏览器播放
            if content_type.startswith('audio/'):
                headers['Content-Disposition'] = 'inline'
        
        try:
            # 上传到OSS
            logger.info(f'开始上传文件到OSS: {full_path}, 大小: {file_size} 字节, Content-Type: {content_type}')
            result = self.bucket.put_object(full_path, file_content, headers=headers)
            logger.info(f'文件上传成功: {full_path}, ETag: {result.etag}')
            return name
        except Exception as e:
            logger.error(f'文件上传失败: {full_path}, 错误: {str(e)}')
            raise
    
    def exists(self, name):
        """检查文件是否存在"""
        full_path = self._get_full_path(name)
        return self.bucket.object_exists(full_path)
    
    def url(self, name):
        """获取文件URL"""
        import logging
        from urllib.parse import quote
        logger = logging.getLogger(__name__)
        
        if not name:
            return ''
        full_path = self._get_full_path(name)
        
        # 使用保存的实际endpoint（如果已初始化bucket）
        # 优先使用实际连接时确定的endpoint，确保URL使用正确的区域endpoint
        if hasattr(self, '_actual_endpoint') and self._actual_endpoint:
            endpoint_clean = self._actual_endpoint
        else:
            # 如果还未初始化bucket，先初始化以获取正确的endpoint
            _ = self.bucket  # 触发初始化
            if hasattr(self, '_actual_endpoint') and self._actual_endpoint:
                endpoint_clean = self._actual_endpoint
            else:
                # 如果初始化失败，使用配置的endpoint
                endpoint_clean = self.endpoint.replace('https://', '').replace('http://', '').strip('/')
        
        # 对于音频文件，使用签名URL来设置Content-Disposition为inline，允许浏览器播放
        if name.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma')):
            try:
                # 生成签名URL，设置Content-Disposition为inline
                # 注意：sign_url会自动处理路径编码，不需要手动编码
                # 签名URL有效期24小时
                params = {
                    'response-content-disposition': 'inline'
                }
                # 使用原始路径，让sign_url自己处理编码
                url = self.bucket.sign_url('GET', full_path, 24 * 3600, params=params)
                # 确保URL使用HTTPS协议
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://', 1)
                logger.debug(f'生成OSS签名URL（音频文件）: {url} (文件: {name})')
                return url
            except Exception as e:
                logger.warning(f'生成签名URL失败，使用普通URL: {str(e)}')
                # 如果签名URL生成失败，回退到普通URL
                # URL编码路径中的中文字符和特殊字符
                path_parts = full_path.split('/')
                encoded_parts = [quote(part, safe='') for part in path_parts]
                encoded_path = '/'.join(encoded_parts)
                url = f"https://{self.bucket_name}.{endpoint_clean}/{encoded_path}"
        elif name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')):
            # 图片文件也使用签名URL（因为OSS bucket是私有的）
            # 签名URL有效期7天，减少签名生成频率
            try:
                url = self.bucket.sign_url('GET', full_path, 7 * 24 * 3600)
                # 确保URL使用HTTPS协议
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://', 1)
                logger.debug(f'生成OSS签名URL（图片文件）: {url} (文件: {name})')
                return url
            except Exception as e:
                logger.warning(f'生成图片签名URL失败，使用普通URL: {str(e)}')
                # 如果签名URL生成失败，回退到普通URL
                path_parts = full_path.split('/')
                encoded_parts = [quote(part, safe='') for part in path_parts]
                encoded_path = '/'.join(encoded_parts)
                url = f"https://{self.bucket_name}.{endpoint_clean}/{encoded_path}"
        else:
            # 其他文件类型（如视频）也使用签名URL
            # 签名URL有效期7天
            try:
                url = self.bucket.sign_url('GET', full_path, 7 * 24 * 3600)
                # 确保URL使用HTTPS协议
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://', 1)
                logger.debug(f'生成OSS签名URL（其他文件）: {url} (文件: {name})')
                return url
            except Exception as e:
                logger.warning(f'生成签名URL失败，使用普通URL: {str(e)}')
                # 如果签名URL生成失败，回退到普通URL
                path_parts = full_path.split('/')
                encoded_parts = [quote(part, safe='') for part in path_parts]
                encoded_path = '/'.join(encoded_parts)
                url = f"https://{self.bucket_name}.{endpoint_clean}/{encoded_path}"
        
        logger.debug(f'生成OSS URL: {url} (文件: {name}, 完整路径: {full_path}, endpoint: {endpoint_clean})')
        return url
    
    def delete(self, name):
        """删除文件"""
        full_path = self._get_full_path(name)
        try:
            self.bucket.delete_object(full_path)
        except Exception:
            pass
    
    def size(self, name):
        """获取文件大小"""
        full_path = self._get_full_path(name)
        try:
            meta = self.bucket.head_object(full_path)
            return meta.content_length
        except Exception:
            return 0


# 音频文件存储
audio_storage = OSSStorage(base_path='audio')

# 图片文件存储
image_storage = OSSStorage(base_path='images')

# 视频文件存储
video_storage = OSSStorage(base_path='videos')

