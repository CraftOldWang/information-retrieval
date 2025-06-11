# NKU搜索引擎后端服务

南开大学搜索引擎的后端API服务，基于FastAPI构建，提供搜索、用户管理、个性化推荐等功能。

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Elasticsearch 7.0+（运行在localhost:9200）
- SQLite（自动创建）

### 2. 安装依赖

```bash
使用的是根目录下的依赖文件
因为爬虫和后端python环境不冲突，没必要分别弄。
```

### 3. 启动服务

```bash
# 方式1：使用启动脚本
python start_server.py

# 方式2：直接使用uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4. 访问API文档

服务启动后，访问以下地址：

- **Swagger文档**: http://127.0.0.1:8000/docs
- **ReDoc文档**: http://127.0.0.1:8000/redoc
- **健康检查**: http://127.0.0.1:8000/health

## 📚 API功能

### 搜索服务

#### 1. 基础搜索
```http
GET /api/v1/search/?q=南开大学&page=1&page_size=10
```

#### 2. 短语搜索
```http
GET /api/v1/search/?q="南开大学"&search_type=phrase
```

#### 3. 通配符搜索
```http
GET /api/v1/search/?q=南开*&search_type=wildcard
```

#### 4. 文档搜索
```http
GET /api/v1/documents/?q=课程表&doc_type=pdf
```

#### 5. 搜索建议
```http
GET /api/v1/search/suggest?q=南开&limit=10
```

### 用户系统

#### 1. 用户注册
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "username": "student123",
  "email": "student@nankai.edu.cn",
  "password": "password123",
  "college": "计算机学院",
  "major": "计算机科学与技术",
  "grade": "2021"
}
```

#### 2. 用户登录
```http
POST /api/v1/users/login
Content-Type: application/json

{
  "username": "student123",
  "password": "password123"
}
```

#### 3. 获取用户信息
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

### 搜索历史

#### 1. 获取历史记录
```http
GET /api/v1/history/?page=1&page_size=10
Authorization: Bearer <access_token>
```

#### 2. 删除历史记录
```http
DELETE /api/v1/history/123
Authorization: Bearer <access_token>
```

### 个性化推荐

#### 1. 查询推荐
```http
GET /api/v1/recommendations/queries?q=南开&limit=10
```

#### 2. 相关查询
```http
GET /api/v1/recommendations/related?q=南开大学&limit=5
```

#### 3. 热门查询
```http
GET /api/v1/recommendations/popular?limit=10
```

### 网页快照

#### 1. 查看快照
```http
GET /api/v1/snapshots/{url_id}
```

#### 2. 快照信息
```http
GET /api/v1/snapshots/info/{url_id}
```

## 🧪 测试API

运行测试脚本：

```bash
python test_api.py
```

该脚本会测试所有主要API端点的功能。

## 🗂️ 项目结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py          # 路由聚合
│   │       └── endpoints/      # API端点
│   ├── core/
│   │   ├── config.py          # 配置
│   │   └── logging.py         # 日志
│   ├── models/
│   │   └── schemas.py         # 数据模型
│   └── services/
│       ├── elasticsearch_service.py  # 搜索服务
│       ├── user_service.py           # 用户服务
│       ├── history_service.py        # 历史服务
│       ├── recommendation_service.py # 推荐服务
│       └── database_service.py       # 数据库服务
├── main.py                    # FastAPI应用入口
├── start_server.py           # 启动脚本
├── test_api.py              # API测试脚本
└── requirements.txt         # 依赖包
```

## ⚙️ 配置说明

主要配置在 `app/core/config.py` 中：

```python
# 服务器配置
HOST = "127.0.0.1"
PORT = 8000

# Elasticsearch配置
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200

# 数据库配置
SQLITE_DATABASE_URL = "../data/sqlite/nku_search.db"

# JWT配置
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

## 🔧 开发说明

### 添加新的API端点

1. 在 `app/api/v1/endpoints/` 中创建新的路由文件
2. 在 `app/api/v1/api.py` 中注册路由
3. 在 `app/services/` 中实现业务逻辑
4. 在 `app/models/schemas.py` 中定义数据模型

### 数据库操作

数据库自动初始化，表结构在 `app/services/database_service.py` 中定义。

### 搜索功能扩展

搜索逻辑在 `app/services/elasticsearch_service.py` 中实现，可以扩展查询DSL。

## 🐛 故障排除

### 1. Elasticsearch连接失败

确保Elasticsearch服务正在运行：
```bash
curl http://localhost:9200
```

### 2. 数据库错误

检查数据目录权限，数据库文件会自动创建在 `../data/sqlite/` 目录。

### 3. 模块导入错误

确保在 `backend` 目录下运行服务，并且已安装所有依赖。

## 📝 开发日志

- ✅ 基础搜索功能
- ✅ 用户认证系统
- ✅ 搜索历史管理
- ✅ 推荐系统
- ✅ 网页快照功能
- ✅ API文档和测试

## 🤝 贡献

这是南开大学信息检索课程作业项目，欢迎提出改进建议。
