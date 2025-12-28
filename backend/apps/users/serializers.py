"""
用户序列化器
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    vip_type_display = serializers.SerializerMethodField()
    is_vip_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('user_id', 'phone', 'nickname', 'avatar_url', 'is_vip', 
                  'vip_type', 'vip_type_display', 'vip_expire_at', 'coin_balance', 
                  'date_joined', 'is_vip_valid')
        read_only_fields = ('user_id', 'date_joined')
    
    def get_vip_type_display(self, obj):
        """获取VIP类型显示名称"""
        if not obj.is_vip or not obj.vip_type:
            return None
        vip_type_map = {
            'monthly': '月度VIP',
            'quarterly': '季度VIP',
            'yearly': '年度VIP',
            'lifetime': '终身VIP',
            'trial': '体验VIP',
        }
        return vip_type_map.get(obj.vip_type, obj.vip_type)
    
    def get_is_vip_valid(self, obj):
        """检查VIP是否有效"""
        return obj.is_vip_valid


class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('phone', 'password', 'password_confirm', 'nickname')
    
    def validate(self, attrs):
        """验证密码确认"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "两次密码输入不一致"})
        return attrs
    
    def create(self, validated_data):
        """创建用户"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            phone=validated_data['phone'],
            password=validated_data['password'],
            nickname=validated_data.get('nickname', '')
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    
    class Meta:
        model = User
        fields = ('user_id', 'phone', 'nickname', 'avatar_url', 'is_vip', 
                  'vip_type', 'vip_expire_at', 'coin_balance', 'date_joined')
        read_only_fields = ('user_id', 'phone', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """验证密码确认"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "两次新密码输入不一致"})
        return attrs
    
    def validate_old_password(self, value):
        """验证旧密码"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码错误")
        return value

