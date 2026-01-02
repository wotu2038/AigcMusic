import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/auth';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import './Register.css';

function Register() {
    const navigate = useNavigate();
    const [phone, setPhone] = useState('');
    const [nickname, setNickname] = useState('');
    const [password, setPassword] = useState('');
    const [passwordConfirm, setPasswordConfirm] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        
        // 验证密码
        if (password !== passwordConfirm) {
            setError('两次密码输入不一致');
            return;
        }
        
        if (password.length < 8) {
            setError('密码长度至少8位');
            return;
        }
        
        setLoading(true);
        
        try {
            await authService.register(phone, password, passwordConfirm, nickname);
            // 注册成功，跳转到首页
            navigate('/');
        } catch (err) {
            console.error('注册错误:', err);
            console.error('错误响应:', err.response);
            
            // 处理后端返回的错误信息
            const errorData = err.response?.data;
            
            if (errorData?.errors) {
                // 如果有详细的错误信息，收集所有错误
                const errorMessages = [];
                Object.keys(errorData.errors).forEach(field => {
                    const fieldErrors = errorData.errors[field];
                    if (Array.isArray(fieldErrors)) {
                        errorMessages.push(...fieldErrors);
                    } else if (typeof fieldErrors === 'string') {
                        errorMessages.push(fieldErrors);
                    }
                });
                
                if (errorMessages.length > 0) {
                    // 显示所有错误，用换行分隔
                    setError(errorMessages.join('；'));
                } else {
                    setError(errorData.message || '注册失败，请重试');
                }
            } else if (errorData?.message) {
                setError(errorData.message);
            } else if (err.message) {
                setError(`注册失败：${err.message}`);
            } else {
                setError('注册失败，请检查网络连接后重试');
            }
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <Loading text="注册中..." />;
    }
    
    return (
        <div className="register-container">
            <div className="register-card">
                <h2>🎵 MusiMusi</h2>
                <p className="register-subtitle">创建您的音乐账户</p>
                
                <ErrorMessage message={error} onClose={() => setError('')} />
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="phone">手机号</label>
                        <input
                            id="phone"
                            type="tel"
                            value={phone}
                            onChange={(e) => setPhone(e.target.value)}
                            placeholder="请输入手机号"
                            required
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="nickname">昵称（可选）</label>
                        <input
                            id="nickname"
                            type="text"
                            value={nickname}
                            onChange={(e) => setNickname(e.target.value)}
                            placeholder="请输入昵称"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="password">密码</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="请输入密码（至少8位）"
                            required
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="passwordConfirm">确认密码</label>
                        <input
                            id="passwordConfirm"
                            type="password"
                            value={passwordConfirm}
                            onChange={(e) => setPasswordConfirm(e.target.value)}
                            placeholder="请再次输入密码"
                            required
                        />
                    </div>
                    
                    <button type="submit" className="btn" style={{ width: '100%' }}>
                        注册
                    </button>
                </form>
                
                <p className="register-link">
                    已有账户？<a href="/login">立即登录</a>
                </p>
            </div>
        </div>
    );
}

export default Register;

