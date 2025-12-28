"""
用户模型
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# VIP类型选择
VIP_TYPE_CHOICES = [
    ('monthly', '月度VIP'),
    ('quarterly', '季度VIP'),
    ('yearly', '年度VIP'),
    ('lifetime', '终身VIP'),
    ('trial', '体验VIP'),
]


class UserManager(BaseUserManager):
    """自定义用户管理器"""
    
    def create_user(self, phone, password=None, **extra_fields):
        """创建普通用户"""
        if not phone:
            raise ValueError('手机号是必填项')
        
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')
        
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """用户模型"""
    user_id = models.AutoField(primary_key=True, verbose_name='用户ID')
    phone = models.CharField(max_length=20, unique=True, verbose_name='手机号')
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    avatar_url = models.URLField(blank=True, null=True, verbose_name='头像URL')
    
    # VIP相关
    is_vip = models.BooleanField(default=False, verbose_name='是否VIP')
    vip_type = models.CharField(
        max_length=20,
        choices=VIP_TYPE_CHOICES,
        default='monthly',
        blank=True,
        null=True,
        verbose_name='VIP类型'
    )
    vip_expire_at = models.DateTimeField(null=True, blank=True, verbose_name='VIP到期时间')
    
    # 金币余额
    coin_balance = models.PositiveIntegerField(default=0, verbose_name='金币余额')
    
    # Django认证相关
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_staff = models.BooleanField(default=False, verbose_name='是否员工')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='注册时间')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.phone
    
    @property
    def is_vip_valid(self):
        """检查VIP是否有效"""
        if not self.is_vip:
            return False
        if self.vip_expire_at and self.vip_expire_at < timezone.now():
            return False
        return True

