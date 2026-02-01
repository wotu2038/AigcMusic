# AigcMusic 项目

## 📋 项目简介

AigcMusic 是一个基于 Django 的全栈音乐应用项目，集成了 AI 生成内容（AIGC）功能。项目支持音乐播放、评论互动，并利用阿里云万相（通义万相）API 自动生成歌词配图、评论摘要、歌词视频等多种 AIGC 内容。

### 核心功能

- 🎵 **音乐播放**：支持在线播放音乐，提供完整的播放器功能
- 💬 **评论系统**：支持评论、回复、点赞，支持嵌套回复（最多2层）
- 🤖 **AI 评论回复**：用户可以通过 `@AI` 触发 AI 自动回复评论
- 🎨 **AIGC 内容生成**：
  - 歌词配图：基于歌词自动生成配图
  - 评论摘要：自动生成评论摘要
  - 歌词视频：图生视频（基于歌词配图生成视频）
  - 文生视频：直接基于文本描述生成视频
- 📱 **响应式设计**：支持 Web 和移动端访问

## 🚀 快速开始

### 环境配置

1. 复制环境配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，替换所有占位符为实际配置值：
   - **数据库配置**：RDS 地址、数据库名、用户名、密码
   - **OSS 配置**：AccessKey、Secret、Bucket 名称
   - **Redis 配置**：密码
   - **Django 配置**：Secret Key、Debug 模式、Allowed Hosts
   - **阿里万相配置**：API Key、Secret、Endpoint
   - **CORS 配置**：允许的前端域名
   
   详细配置说明请参考 `.env.example` 文件中的注释。

3. 启动服务：
   ```bash
   docker-compose up -d
   ```

### 访问地址

**开发环境**：
- **Web前端**: http://localhost:8025
- **Django Admin**: http://localhost:8025/admin/
- **REST API**: http://localhost:8025/api/
- **API文档**: http://localhost:8025/api/docs/

**生产环境**（使用相同端口号）：
- **Web前端**: http://your-production-ip:8025 或 https://your-production-ip:8443
- **Django Admin**: http://your-production-ip:8025/admin/
- **REST API**: http://your-production-ip:8025/api/
- **API文档**: http://your-production-ip:8025/api/docs/

---

## 🛠️ 开发环境快速启动指南

### 快速启动（3步）

#### 1. 启动后端服务

```bash
docker-compose up -d web redis
```

**验证**：
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web
```

**访问**：
- API文档：http://localhost:8025/api/docs/
- Admin：http://localhost:8025/admin/

#### 2. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

**访问**：
- 前端应用：http://localhost:3000

#### 3. 开始开发

打开浏览器访问：http://localhost:3000

---

### 服务说明

#### 后端服务（Django）

- **容器名**：`aigcmusic-web`
- **端口**：8025（外部）→ 8000（容器内）
- **功能**：REST API + Django Admin
- **认证**：JWT Token

#### 前端服务（React）

- **端口**：3000
- **功能**：React SPA
- **代理**：`/api` → `http://localhost:8025/api`

#### Redis服务

- **容器名**：`aigcmusic-redis`
- **端口**：6379
- **功能**：缓存、Celery消息队列

#### Celery服务

- **容器名**：`aigcmusic-celery`
- **功能**：异步任务处理（AIGC内容生成、AI评论回复等）

#### Celery Beat服务

- **容器名**：`aigcmusic-celery-beat`
- **功能**：定时任务调度

---

### 常用命令

#### 后端

```bash
# 启动服务
docker-compose up -d web redis

# 停止服务
docker-compose stop web redis

# 查看日志
docker-compose logs -f web

# 重启服务
docker-compose restart web

# 进入容器
docker-compose exec web bash

# 运行Django命令
docker-compose exec web python manage.py <command>
```

#### 前端

```bash
# 启动开发服务器
cd frontend && npm run dev

# 构建生产版本
cd frontend && npm run build

# 预览生产版本
cd frontend && npm run preview
```

---

### 故障排查

#### 后端无法启动

```bash
# 检查日志
docker-compose logs web

# 检查数据库连接
docker-compose exec web python manage.py check

# 重新构建
docker-compose build web
```

#### 前端无法启动

```bash
# 检查端口占用
lsof -ti:3000

# 清除缓存
cd frontend && rm -rf node_modules && npm install

# 检查配置
cat frontend/vite.config.js
```

#### API无法访问

```bash
# 测试API
curl http://localhost:8025/api/songs/

# 检查CORS配置
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.CORS_ALLOWED_ORIGINS)
```

#### 连接重置错误（ERR_CONNECTION_RESET）

如果访问 `http://your-ip:8025` 出现连接重置错误，通常是因为nginx服务未启动：

```bash
# 1. 检查nginx服务状态
docker compose ps | grep nginx

# 2. 如果nginx未启动，启动nginx和frontend服务
docker compose --profile production up -d nginx frontend

# 3. 验证服务状态
docker compose ps

# 4. 检查端口是否监听
netstat -tlnp | grep 8025
# 或
ss -tlnp | grep 8025

# 5. 检查nginx日志
docker compose logs nginx --tail 50
```

**注意**：生产环境必须启动nginx服务，因为：
- nginx作为反向代理，统一处理所有请求
- web服务的端口在生产环境配置中被注释掉了
- 所有请求（前端、API、Admin）都通过nginx转发

#### celery-beat 权限错误

如果 `celery-beat` 服务不断重启，日志中出现 `Permission denied: '/app/celerybeat/celerybeat-schedule'` 错误：

```bash
# 1. 检查celery-beat日志
docker compose logs celery-beat --tail 50

# 2. 如果看到权限错误，在宿主机上创建目录并设置权限
cd /opt/AigcMusic/backend  # 或你的项目路径
mkdir -p celerybeat
chmod 777 celerybeat

# 3. 重启celery-beat服务
docker compose restart celery-beat

# 4. 验证服务启动成功
docker compose logs celery-beat --tail 20
# 应该看到：beat: Starting...
```

**如果还有问题，可以尝试：**

```bash
# 删除可能存在的旧文件
cd /opt/AigcMusic/backend
rm -rf celerybeat
mkdir -p celerybeat
chmod 777 celerybeat

# 完全重启服务
cd /opt/AigcMusic
docker compose down
docker compose up -d

# 查看日志
docker compose logs celery-beat --tail 50
```

**原因说明**：
- `/app` 目录通过 volume 挂载到宿主机的 `./backend:/app`
- 容器内以 `django` 用户（UID 1000）运行
- 宿主机上的目录可能属于 root 用户，容器内用户无权限写入
- 需要预先创建目录并设置适当权限

**持久化说明**：
- 调度文件存储在 `backend/celerybeat/` 目录中
- 该目录会持久化到宿主机，容器重启后不会丢失调度信息

## 📚 文档

> **注意**：项目文档位于 `docs/` 文件夹中，但该文件夹已配置为不提交到 Git 仓库（见 `.gitignore`）。

如需查看详细文档，请参考项目中的 `docs/` 目录。

## 🔧 技术栈

### 后端
- **框架**: Django + Django REST Framework
- **数据库**: MySQL 8.0 (阿里云RDS)
- **缓存**: Redis 7
- **任务队列**: Celery + Celery Beat
- **对象存储**: 阿里云OSS
- **AI服务**: 阿里云万相（通义万相）API
  - 图像生成：wanx-v1
  - 文本生成：qwen-turbo
  - 视频生成：wan2.2-i2v-plus

### 前端
- **框架**: React 18
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **路由**: React Router

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx（生产环境）

## 📝 环境配置说明

所有配置都在 `.env` 文件中，Docker 会自动读取。项目提供了 `.env.example` 文件作为配置模板。

### 配置步骤

1. **复制配置模板**：
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**，替换所有占位符为实际值：
   - 数据库配置（RDS 地址、数据库名、用户名、密码）
   - OSS 配置（AccessKey、Secret、Bucket 名称）
   - Redis 配置（密码）
   - Django 配置（Secret Key、Debug 模式）
   - 阿里万相配置（API Key、Secret）
   - CORS 配置（允许的前端域名）
   - 服务端口配置（WEB_PORT、HTTPS_PORT）

3. **开发/生产环境切换**：
   - 开发环境：使用激活的配置项
   - 生产环境：取消注释生产环境配置，注释掉开发环境配置

### 重要提示

- ⚠️ **不要将 `.env` 文件提交到 Git 仓库**（已在 `.gitignore` 中配置）
- ✅ `.env.example` 文件已使用占位符，可以安全提交
- 🔒 生产环境请使用强密码和安全的 Secret Key

---

## 🚀 生产环境部署指南

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 已配置阿里云 RDS MySQL 数据库
- 已配置阿里云 OSS 存储桶
- 服务器已开放所需端口（8025、8443）

### 部署步骤

#### 1. 准备服务器环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 克隆项目

```bash
# 克隆项目到服务器
git clone <your-repo-url> /opt/aigcmusic
cd /opt/aigcmusic
```

#### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，配置生产环境
nano .env
```

**生产环境配置示例**（在 `.env` 文件中，注释掉开发环境配置，取消注释生产环境配置）：
```env
# 数据库配置（注释掉开发环境，取消注释生产环境）
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=your-db-name-dev
# DB_USER=your-db-user
# DB_PASSWORD=your-db-password
# DB_HOST=your-rds-host.mysql.rds.aliyuncs.com
# DB_PORT=3306

DB_ENGINE=django.db.backends.mysql
DB_NAME=your-db-name-prod
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-production-rds-host.mysql.rds.aliyuncs.com
DB_PORT=3306

# OSS配置（注释掉开发环境，取消注释生产环境）
# OSS_ACCESS_KEY_ID=your-oss-access-key-id
# OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret
# OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
# OSS_BUCKET_NAME=your-oss-bucket-name-dev

OSS_ACCESS_KEY_ID=your-oss-access-key-id
OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret
OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
OSS_BUCKET_NAME=your-oss-bucket-name-prod

# Django配置（注释掉开发环境，取消注释生产环境）
# DJANGO_SECRET_KEY=your-secret-key-change-in-production
# DJANGO_DEBUG=True
# DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DJANGO_SECRET_KEY=your-production-secret-key-change-this
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-production-ip,localhost,127.0.0.1

# CORS配置（注释掉开发环境，取消注释生产环境）
# CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80

CORS_ALLOWED_ORIGINS=http://your-production-ip:8025,https://your-production-ip:8443

# 服务端口配置（开发和生产环境可以使用相同端口）
WEB_PORT=8025
HTTPS_PORT=8443

# 前端API配置（注释掉开发环境，取消注释生产环境）
# VITE_API_URL=http://localhost:8025/api

VITE_API_URL=http://your-production-ip:8025/api
# 或者如果使用HTTPS：
# VITE_API_URL=https://your-production-ip:8443/api
```

#### 4. 配置RDS白名单

1. 登录 [阿里云RDS控制台](https://rds.console.aliyun.com/)
2. 选择您的RDS实例
3. 进入"数据安全性" -> "白名单设置"
4. 添加服务器公网IP或 `0.0.0.0/0`（仅用于测试，生产环境建议使用具体IP）

#### 5. 构建和启动服务

```bash
# 构建Docker镜像
docker-compose build

# 启动基础服务（web、redis、celery、celery-beat）
docker-compose up -d

# 启动生产环境服务（包含Nginx反向代理和前端）
docker-compose --profile production up -d nginx frontend
```

**重要提示**：
- 生产环境必须启动 `nginx` 和 `frontend` 服务才能正常访问
- 如果访问 `http://your-ip:8025` 出现连接重置错误，请检查是否已启动nginx服务：
  ```bash
  # 检查nginx服务状态
  docker compose ps | grep nginx
  
  # 如果nginx未启动，执行：
  docker compose --profile production up -d nginx frontend
  ```

#### 6. 初始化数据库

```bash
# 执行数据库迁移
docker-compose exec web python manage.py migrate

# 创建超级用户（用于访问Django Admin）
docker-compose exec web python manage.py createsuperuser

# 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput
```

#### 7. 验证服务

```bash
# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f web

# 测试API
curl http://your-production-ip:8025/api/songs/
```

#### 8. 访问服务

- **Web前端**: http://your-production-ip:8025
- **Django Admin**: http://your-production-ip:8025/admin/
- **REST API**: http://your-production-ip:8025/api/
- **API文档**: http://your-production-ip:8025/api/docs/

---

### 更新代码（Git Pull）

当GitHub上有新代码时，在ECS服务器上更新：

#### 方法一：拉取最新代码并重启服务（推荐）

```bash
# 1. 进入项目目录
cd /opt/aigcmusic

# 2. 拉取最新代码
git pull origin main

# 3. 如果有Dockerfile变更，需要重新构建
docker-compose build

# 4. 重启基础服务（零停机时间，滚动更新）
docker-compose up -d --build

# 5. 确保nginx和frontend服务已启动（生产环境必需）
docker-compose --profile production up -d nginx frontend

# 6. 如果有数据库迁移，执行迁移
docker-compose exec web python manage.py migrate

# 7. 如果有静态文件变更，收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 8. 验证服务
docker-compose ps
docker-compose logs -f web
docker-compose logs -f nginx
```

#### 方法二：仅拉取代码（不重启服务）

```bash
# 1. 进入项目目录
cd /opt/aigcmusic

# 2. 拉取最新代码
git pull origin main

# 注意：如果只是代码变更（非配置变更），Docker volume挂载会自动更新
# 但需要重启服务才能生效：
docker-compose restart web celery celery-beat
```

#### 方法三：完整更新流程（包含前端构建）

```bash
# 1. 进入项目目录
cd /opt/aigcmusic

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建所有服务（包括前端）
docker-compose build

# 4. 停止旧服务
docker-compose --profile production down

# 5. 启动新服务
docker-compose --profile production up -d

# 6. 执行数据库迁移（如果有）
docker-compose exec web python manage.py migrate

# 7. 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 8. 验证服务
docker-compose ps
```

#### 更新时的注意事项

1. **备份数据**（重要）：
   ```bash
   # 备份数据库（如果使用本地数据库）
   docker-compose exec web python manage.py dumpdata > backup_$(date +%Y%m%d).json
   ```

2. **检查变更**：
   ```bash
   # 查看Git变更
   git log --oneline -5
   git diff HEAD~1
   ```

3. **测试环境验证**：
   - 建议先在测试环境验证更新
   - 确认无误后再在生产环境更新

4. **回滚方法**：
   ```bash
   # 如果更新后出现问题，可以回滚到上一个版本
   git log --oneline  # 查看提交历史
   git checkout <previous-commit-hash>  # 回滚到指定提交
   docker-compose --profile production up -d --build
   ```

---

### 常用运维命令

### 生产环境常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f nginx

# 重启服务
docker-compose restart web
docker-compose restart celery

# 停止服务
docker-compose stop

# 更新代码后重新部署
git pull
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

### 生产环境注意事项

1. **安全配置**：
   - ✅ 使用强密码和安全的 Secret Key
   - ✅ 配置防火墙，只开放必要端口
   - ✅ 定期更新系统和依赖
   - ✅ 配置HTTPS（推荐使用8443端口）

2. **性能优化**：
   - ✅ 配置Nginx反向代理（已包含在生产环境配置中）
   - ✅ 启用Redis缓存
   - ✅ 配置Celery异步任务处理
   - ✅ 定期清理日志和临时文件

3. **监控和维护**：
   - ✅ 配置日志轮转
   - ✅ 监控服务健康状态
   - ✅ 定期备份数据库
   - ✅ 监控磁盘空间和内存使用

## 🎯 主要功能

### AIGC 内容生成

项目支持以下 AIGC 内容生成类型：

1. **歌词配图** (`lyric_image`)：基于歌曲歌词自动生成配图
2. **评论摘要** (`comment_summary`)：自动生成评论摘要
3. **歌词视频** (`lyric_video`)：基于歌词配图生成视频（图生视频）
4. **文生视频** (`text_to_video`)：直接基于文本描述生成视频

### AI 评论回复

用户可以在评论中使用 `@AI` 触发 AI 自动回复，系统会：
- 自动识别评论中的 `@AI` 标记
- 调用千问大模型生成回复
- 以 AI 助手身份发布回复（带 AI 标识）

## 🔐 安全说明

- 所有敏感配置都从 `.env` 文件读取，不硬编码在代码中
- `.env` 文件已添加到 `.gitignore`，不会被提交到仓库
- 生产环境请确保使用强密码和安全的配置

