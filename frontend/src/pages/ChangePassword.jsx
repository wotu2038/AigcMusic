import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import './ChangePassword.css';

function ChangePassword() {
    const navigate = useNavigate();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess(false);
        
        // 验证密码
        if (newPassword !== newPasswordConfirm) {
            setError('两次新密码输入不一致');
            return;
        }
        
        if (newPassword.length < 8) {
            setError('密码长度至少8位');
            return;
        }
        
        setLoading(true);
        
        try {
            await api.post('/users/change-password/', {
                old_password: oldPassword,
                new_password: newPassword
            });
            setSuccess(true);
            setTimeout(() => {
                // 修改密码成功后，需要重新登录
                localStorage.clear();
                navigate('/login');
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.message || '修改密码失败');
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <Loading text="修改密码中..." />;
    }
    
    return (
        <div className="change-password-container">
            <div className="change-password-card">
                <h2>修改密码</h2>
                
                {success ? (
                    <div className="success-message">
                        <p>✅ 密码修改成功，即将跳转到登录页...</p>
                    </div>
                ) : (
                    <>
                        <ErrorMessage message={error} onClose={() => setError('')} />
                        
                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label htmlFor="oldPassword">旧密码</label>
                                <input
                                    id="oldPassword"
                                    type="password"
                                    value={oldPassword}
                                    onChange={(e) => setOldPassword(e.target.value)}
                                    placeholder="请输入旧密码"
                                    required
                                />
                            </div>
                            
                            <div className="form-group">
                                <label htmlFor="newPassword">新密码</label>
                                <input
                                    id="newPassword"
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    placeholder="请输入新密码（至少8位）"
                                    required
                                />
                            </div>
                            
                            <div className="form-group">
                                <label htmlFor="newPasswordConfirm">确认新密码</label>
                                <input
                                    id="newPasswordConfirm"
                                    type="password"
                                    value={newPasswordConfirm}
                                    onChange={(e) => setNewPasswordConfirm(e.target.value)}
                                    placeholder="请再次输入新密码"
                                    required
                                />
                            </div>
                            
                            <button type="submit" className="btn" style={{ width: '100%' }}>
                                修改密码
                            </button>
                        </form>
                    </>
                )}
            </div>
        </div>
    );
}

export default ChangePassword;

