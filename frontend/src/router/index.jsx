import { Routes, Route, Navigate } from 'react-router-dom';
import authService from '../services/auth';

// 页面组件
import SongList from '../pages/SongList';
import SongDetail from '../pages/SongDetail';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Profile from '../pages/Profile';
import ChangePassword from '../pages/ChangePassword';

/**
 * 路由守卫组件：保护需要登录的页面
 */
function PrivateRoute({ children }) {
    return authService.isAuthenticated() ? children : <Navigate to="/login" replace />;
}

/**
 * 路由配置（BrowserRouter已在App.jsx中）
 */
function AppRouter() {
    return (
        <Routes>
            {/* 公开路由 */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<SongList />} />
            <Route path="/songs/:id" element={<SongDetail />} />
            
            {/* 需要登录的路由 */}
            <Route
                path="/profile"
                element={
                    <PrivateRoute>
                        <Profile />
                    </PrivateRoute>
                }
            />
            <Route
                path="/change-password"
                element={
                    <PrivateRoute>
                        <ChangePassword />
                    </PrivateRoute>
                }
            />
            
            {/* 404页面 */}
            <Route path="*" element={<div>404 - 页面不存在</div>} />
        </Routes>
    );
}

export default AppRouter;

