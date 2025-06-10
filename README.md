# 开发环境设置指南

## 项目结构说明

本项目采用模块化架构，每个模块有独立的依赖管理：

```
nku-search-engine/
├── crawler/              # 爬虫模块 (Python + Scrapy)
│   ├── requirements.txt  # 爬虫模块Python依赖
│   └── nku_spider/       # Scrapy项目
├── backend/              # 后端模块 (Python + FastAPI)
│   ├── requirements.txt  # 后端模块Python依赖
│   ├── main.py          # FastAPI应用入口
│   └── app/             # 应用代码
├── frontend/             # 前端模块 (React + TypeScript)
│   ├── package.json     # 前端模块Node.js依赖
│   └── src/             # React源代码
├── config/               # 配置文件
│   ├── elasticsearch/   # ES配置
│   └── redis/           # Redis配置
├── data/                 # 数据目录
│   ├── sqlite/          # SQLite数据库
│   ├── logs/            # 日志文件
│   └── raw/             # 原始数据
└── scripts/              # 工具脚本
    └── start.py         # 项目启动脚本
```

## 快速开始

### 1. 环境要求

-   **Python**: 3.10+
-   **Node.js**: 18.0+
-   **Docker**: 最新版
-   **Git**: 用于版本控制

### 2. 克隆项目

```bash
git clone <项目地址>
cd nku-search-engine
```

### 3. 启动 Docker 服务

```bash
# 启动Elasticsearch、Redis、Kibana
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### 4. 安装各模块依赖

#### 爬虫模块

```bash
cd crawler
pip install -r requirements.txt
```

#### 后端模块

```bash
cd backend
pip install -r requirements.txt
```

#### 前端模块

```bash
cd frontend
npm install
```

### 5. 使用启动脚本（推荐）

```bash
# 启动所有服务
python scripts/start.py start --all

# 单独启动某个模块
python scripts/start.py crawler    # 启动爬虫
python scripts/start.py backend    # 启动后端
python scripts/start.py frontend   # 启动前端
python scripts/start.py docker     # 启动Docker服务
```

## 手动启动各服务

### 1. Docker 服务

```bash
docker-compose up -d
```

### 2. 爬虫服务

```bash
cd crawler
scrapy crawl nku_main
```

### 3. 后端服务

```bash
cd backend
python main.py
# 或使用uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4. 前端服务

```bash
cd frontend
npm run dev
```

## 服务访问地址

-   **前端界面**: http://localhost:3000
-   **后端 API**: http://localhost:8000
-   **API 文档**: http://localhost:8000/docs
-   **Elasticsearch**: http://localhost:9200
-   **Kibana**: http://localhost:5601
-   **Redis**: localhost:6379

## 开发工具推荐

### Python 开发

-   **IDE**: PyCharm Professional 或 VS Code
-   **代码格式化**: black, flake8
-   **类型检查**: mypy
-   **测试**: pytest

### Node.js 开发

-   **IDE**: VS Code
-   **包管理**: npm 或 yarn
-   **代码格式化**: prettier, eslint
-   **测试**: jest, @testing-library/react

### 数据库工具

-   **SQLite**: DB Browser for SQLite
-   **Elasticsearch**: Kibana (已包含在 Docker 中)
-   **Redis**: Redis Commander 或 Redis Desktop Manager

## 常见问题

### 1. Docker 容器启动失败

```bash
# 检查端口占用
netstat -an | findstr "9200\|6379\|5601"

# 重新启动服务
docker-compose down
docker-compose up -d
```

### 2. Python 依赖冲突

建议使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate
```

### 3. 前端依赖安装失败

```bash
# 清除缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install
```

## 数据库初始化

### SQLite 数据库

数据库会在后端首次启动时自动创建，位置：`data/sqlite/nku_search.db`

### Elasticsearch 索引

索引会在爬虫首次运行时自动创建，可以通过 Kibana 查看：

1. 访问 http://localhost:5601
2. 进入 "Stack Management" > "Index Management"
3. 查看 `nku_webpages` 索引

## 代码规范

### Python 代码规范

-   使用 `black` 进行代码格式化
-   使用 `flake8` 进行代码检查
-   使用类型注解提高代码质量
-   遵循 PEP 8 规范

### JavaScript/TypeScript 代码规范

-   使用 `prettier` 进行代码格式化
-   使用 `eslint` 进行代码检查
-   使用 TypeScript 进行类型检查
-   遵循 Airbnb 规范

## 测试

### 运行后端测试

```bash
cd backend
pytest
```

### 运行前端测试

```bash
cd frontend
npm test
```

## 部署

### 开发环境

使用本文档的设置即可

### 生产环境

1. 使用 Docker Compose 进行容器化部署
2. 配置反向代理 (Nginx)
3. 设置环境变量和密钥
4. 配置 SSL 证书
5. 设置日志收集和监控
