import api from './api';

class AuthService {
    /**
     * 用户登录
     * @param {string} phone - 手机号
     * @param {string} password - 密码
     * @returns {Promise<{user: object, tokens: object}>}
     */
    async login(phone, password) {
        const response = await api.post('/auth/login/', { phone, password });
        const { tokens, user } = response.data.data;
        
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        localStorage.setItem('user', JSON.stringify(user));
        
        return { user, tokens };
    }
    
    /**
     * 用户注册
     * @param {string} phone - 手机号
     * @param {string} password - 密码
     * @param {string} passwordConfirm - 确认密码
     * @param {string} nickname - 昵称（可选）
     * @returns {Promise<{user: object, tokens: object}>}
     */
    async register(phone, password, passwordConfirm, nickname = '') {
        const response = await api.post('/auth/register/', {
            phone,
            password,
            password_confirm: passwordConfirm,
            nickname
        });
        const { tokens, user } = response.data.data;
        
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        localStorage.setItem('user', JSON.stringify(user));
        
        return { user, tokens };
    }
    
    /**
     * 用户登出
     */
    logout() {
        localStorage.clear();
        window.location.href = '/login';
    }
    
    /**
     * 检查是否已登录
     * @returns {boolean}
     */
    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    }
    
    /**
     * 获取当前用户信息
     * @returns {object|null}
     */
    getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }
    
    /**
     * 获取访问Token
     * @returns {string|null}
     */
    getToken() {
        return localStorage.getItem('access_token');
    }
}

export default new AuthService();

