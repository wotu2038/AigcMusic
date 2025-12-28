# 前端构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 复制package文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY frontend/ .

# 构建生产版本
RUN npm run build

# 生产阶段 - Nginx
FROM nginx:alpine

# 复制构建产物到Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]

