"""
用户视图
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User
from .serializers import (
    UserSerializer, 
    UserRegisterSerializer, 
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """用户注册"""
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # 生成JWT Token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': '注册成功',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': '注册失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """用户登录"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']
        
        # 验证用户
        user = authenticate(request, username=phone, password=password)
        
        if user is not None:
            if user.is_active:
                # 生成JWT Token
                refresh = RefreshToken.for_user(user)
                
                # 更新最后登录时间
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                
                return Response({
                    'success': True,
                    'message': '登录成功',
                    'data': {
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': '账户已被禁用'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'success': False,
                'message': '手机号或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'success': False,
        'message': '登录失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """获取当前用户资料"""
    serializer = UserProfileSerializer(request.user)
    return Response({
        'success': True,
        'message': '获取成功',
        'data': serializer.data
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """更新用户资料"""
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': '更新成功',
            'data': serializer.data
        })
    return Response({
        'success': False,
        'message': '更新失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """用户列表（管理员）"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """用户详情（管理员）"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'user_id'


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """修改密码"""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({
            'success': True,
            'message': '密码修改成功'
        }, status=status.HTTP_200_OK)
    return Response({
        'success': False,
        'message': '密码修改失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

