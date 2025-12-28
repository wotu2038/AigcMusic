import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
    timeout: 10000,
});

// 请求拦截器：自动添加JWT Token
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    error => Promise.reject(error)
);

// 响应拦截器：自动刷新Token
api.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;
        
        // Token过期，尝试刷新
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const res = await axios.post('/api/auth/token/refresh/', {
                        refresh: refreshToken
                    });
                    const newToken = res.data.access;
                    localStorage.setItem('access_token', newToken);
                    
                    // 重试原请求
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // 刷新失败，清除Token并跳转登录
                    localStorage.clear();
                    window.location.href = '/login';
                    return Promise.reject(refreshError);
                }
            } else {
                // 没有refresh token，直接跳转登录
                localStorage.clear();
                window.location.href = '/login';
            }
        }
        
        return Promise.reject(error);
    }
);

export default api;

