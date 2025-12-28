import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import authService from '../services/auth';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import './Login.css';

function Login() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        
        try {
            await authService.login(phone, password);
            // 登录成功，跳转到原页面或首页
            const next = searchParams.get('next') || '/';
            navigate(next);
        } catch (err) {
            setError(err.response?.data?.message || '登录失败，请检查手机号和密码');
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <Loading text="登录中..." />;
    }
    
    return (
        <div className="login-container">
            <div className="login-card">
                <h2>🎵 AigcMusic</h2>
                <p className="login-subtitle">欢迎回来</p>
                
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
                            autoFocus
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="password">密码</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="请输入密码"
                            required
                        />
                    </div>
                    
                    <button type="submit" className="btn" style={{ width: '100%' }}>
                        登录
                    </button>
                </form>
                
                <p className="login-link">
                    还没有账户？<a href="/register">立即注册</a>
                </p>
            </div>
        </div>
    );
}

export default Login;

