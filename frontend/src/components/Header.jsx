import { Link, useNavigate } from 'react-router-dom';
import authService from '../services/auth';
import './Header.css';

/**
 * 顶部导航栏组件
 */
function Header() {
    const navigate = useNavigate();
    const user = authService.getUser();
    const isAuthenticated = authService.isAuthenticated();
    
    const handleLogout = () => {
        if (window.confirm('确定要退出登录吗？')) {
            authService.logout();
        }
    };
    
    return (
        <header className="header">
            <div className="header-content">
                <Link to="/" className="header-logo">
                    <h1>🎵 MusiMusi</h1>
                </Link>
                
                <nav className="header-nav">
                    {isAuthenticated ? (
                        <>
                            <span className="header-user">
                                {user?.nickname || user?.phone}
                            </span>
                            <Link to="/profile" className="header-link">个人资料</Link>
                            <button onClick={handleLogout} className="header-link header-logout">
                                退出
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="header-link">登录</Link>
                            <Link to="/register" className="header-link">注册</Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}

export default Header;

