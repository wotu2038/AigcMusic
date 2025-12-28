import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import authService from '../services/auth';
import api from '../services/api';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import './Profile.css';

function Profile() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    useEffect(() => {
        loadProfile();
    }, []);
    
    const loadProfile = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await api.get('/users/profile/');
            setUser(response.data.data || response.data);
        } catch (err) {
            setError(err.response?.data?.message || '加载用户信息失败');
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <Loading text="加载用户信息..." />;
    }
    
    const currentUser = user || authService.getUser();
    
    return (
        <div className="profile-container">
            <div className="profile-card">
                <h2>个人资料</h2>
                
                <ErrorMessage message={error} onClose={() => setError('')} />
                
                {currentUser && (
                    <div className="profile-info">
                        <div className="profile-item">
                            <span className="profile-label">手机号：</span>
                            <span className="profile-value">{currentUser.phone}</span>
                        </div>
                        
                        <div className="profile-item">
                            <span className="profile-label">昵称：</span>
                            <span className="profile-value">{currentUser.nickname || '未设置'}</span>
                        </div>
                        
                        <div className="profile-item">
                            <span className="profile-label">VIP状态：</span>
                            <span className="profile-value">
                                {currentUser.is_vip ? '✅ VIP' : '普通用户'}
                            </span>
                        </div>
                        
                        <div className="profile-item">
                            <span className="profile-label">金币余额：</span>
                            <span className="profile-value">{currentUser.coin_balance || 0}</span>
                        </div>
                        
                        {currentUser.date_joined && (
                            <div className="profile-item">
                                <span className="profile-label">注册时间：</span>
                                <span className="profile-value">
                                    {new Date(currentUser.date_joined).toLocaleString('zh-CN')}
                                </span>
                            </div>
                        )}
                    </div>
                )}
                
                <div className="profile-actions">
                    <Link to="/change-password" className="btn btn-secondary">
                        修改密码
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default Profile;

