# 技术实现文档

## 系统架构

### 整体架构

NKU Web Search Engine 采用简化的三层架构，适合作业规模：

1. **数据层**: 包括爬虫采集的网页数据、Elasticsearch 索引和 SQLite 用户数据
2. **应用层**: FastAPI 后端服务，处理业务逻辑
3. **表示层**: React 前端界面，提供用户交互

### 架构图

```
+----------------+     +----------------+     +------------------+
|                |     |                |     |                  |
|  React Frontend +<--->+  FastAPI Backend +<--->+  Elasticsearch   |
|                |     |                |     |   (Docker)       |
+----------------+     +-------+--------+     +------------------+
                               |                        
                      +--------v--------+     +------------------+
                      |                 |     |                  |
                      |     SQLite      |     |      Redis       |
                      |   (用户数据)     |     |   (Docker)       |
                      +-----------------+     +------------------+
                               ^                        ^
                               |                        |
                      +--------v------------------------+
                      |                                 |
                      |        Scrapy Crawler          |
                      |                                 |
                      +---------------------------------+
```

## 技术栈详解

### 爬虫模块

-   **Scrapy**: 高效异步爬虫框架
-   **BeautifulSoup/lxml**: 用于 HTML 解析
-   **Requests**: 用于简单的 HTTP 请求

### 索引模块

-   **Elasticsearch 8.x**: 全文搜索引擎
-   **elasticsearch-py**: Elasticsearch 的 Python 客户端
-   **IK 分词器**: 中文分词插件
-   **jieba**: Python 中文分词库，用于预处理

### 后端服务

-   **FastAPI**: 高性能 Python API 框架
-   **Pydantic**: 数据验证和设置管理
-   **uvicorn**: ASGI 服务器
-   **SQLite**: 轻量级数据库，存储用户数据
-   **PyJWT**: JSON Web Token 实现
-   **aiofiles**: 异步文件操作

### 前端界面

-   **React 18**: 用户界面库
-   **Ant Design 5.x**: UI 组件库
-   **axios**: HTTP 客户端
-   **React Router 6**: 前端路由
-   **SCSS**: CSS 预处理器

### 数据库

-   **Elasticsearch**: 存储和索引网页内容 (Docker容器)
-   **Redis**: 缓存查询结果、会话存储、爬虫队列管理 (Docker容器)
-   **SQLite**: 存储用户数据、查询历史和偏好设置 (本地文件)

## 开发环境配置

### 系统要求

-   **操作系统**: Windows/macOS/Linux
-   **Python**: 3.10+
-   **Node.js**: 18.0+
-   **Docker**: 最新版(可选，用于容器化部署)

### 开发环境设置

#### 后端环境

```bash
# 创建虚拟环境
python -m venv venv
# 激活环境
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
# 安装依赖
pip install -r backend/requirements.txt
```

#### 前端环境

```bash
# 进入前端目录
cd frontend
# 安装依赖
npm install
```

### 数据库设置

#### Redis

```bash
# 使用Docker运行Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Redis 用途：
- **查询缓存**: 缓存热门搜索结果，提高响应速度
- **会话存储**: 存储用户登录会话信息
- **爬虫队列**: 分布式爬虫的URL队列和任务调度
- **限流控制**: API访问限流和防刷机制

#### Elasticsearch

```bash
# 使用Docker运行Elasticsearch
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.10.2
# 安装IK分词器
docker exec -it elasticsearch /bin/bash -c "bin/elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.10.2/elasticsearch-analysis-ik-8.10.2.zip"
# 重启Elasticsearch
docker restart elasticsearch
```

#### SQLite

SQLite 是嵌入式数据库，无需额外安装和配置，直接在应用中使用即可。

## 代码组织结构

```
nku-search-engine/
├── crawler/                  # 爬虫模块
│   ├── spiders/              # 爬虫实现
│   ├── pipelines/            # 数据处理管道
│   ├── middlewares/          # 中间件
│   └── settings.py           # 爬虫配置
├── backend/                  # FastAPI后端
│   ├── app/                  # 应用代码
│   │   ├── api/              # API路由
│   │   ├── core/             # 核心功能
│   │   ├── models/           # 数据模型
│   │   └── services/         # 业务服务
│   └── main.py               # 入口文件
├── frontend/                 # React前端
│   ├── public/               # 静态资源
│   ├── src/                  # 源代码
│   │   ├── components/       # UI组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API服务
│   │   └── utils/            # 工具函数
│   └── package.json          # 配置文件
├── config/                   # 配置文件
│   ├── elasticsearch/        # ES配置
│   └── nginx/                # Nginx配置(可选)
└── scripts/                  # 辅助脚本
    ├── setup.sh              # 环境设置脚本
    └── indexing.py           # 索引构建脚本
```

## 核心功能实现细节

### 爬虫实现

```python
# Scrapy爬虫示例
import scrapy
from scrapy.linkextractors import LinkExtractor

class NKUSpider(scrapy.Spider):
    name = 'nku'
    allowed_domains = ['nankai.edu.cn']
    start_urls = ['https://www.nankai.edu.cn/']

    def parse(self, response):
        # 提取页面内容
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'content': ' '.join(response.css('p::text').getall()),
            'html': response.body.decode('utf-8'),
            'crawl_time': datetime.now().isoformat(),
        }

        # 提取锚文本和链接
        link_extractor = LinkExtractor()
        for link in link_extractor.extract_links(response):
            yield {
                'source_url': response.url,
                'target_url': link.url,
                'text': link.text,
            }

        # 提取文档链接
        for href in response.css('a[href$=".pdf"], a[href$=".doc"], a[href$=".docx"]::attr(href)').getall():
            url = response.urljoin(href)
            yield {
                'url': url,
                'type': url.split('.')[-1].lower(),
                'filename': url.split('/')[-1],
                'source_page': response.url,
            }

        # 继续爬取链接
        for href in response.css('a::attr(href)').getall():
            yield response.follow(href, self.parse)
```

### Elasticsearch 索引设置

```python
# 创建索引的Python代码
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

# 创建网页索引
es.indices.create(
    index="webpages",
    body={
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "ik_smart_pinyin": {
                        "type": "custom",
                        "tokenizer": "ik_smart",
                        "filter": ["pinyin_filter"]
                    }
                },
                "filter": {
                    "pinyin_filter": {
                        "type": "pinyin",
                        "keep_full_pinyin": True
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_smart",
                    "fields": {
                        "pinyin": {"type": "text", "analyzer": "ik_smart_pinyin"},
                        "keyword": {"type": "keyword"}
                    }
                },
                "content": {"type": "text", "analyzer": "ik_smart"},
                "domain": {"type": "keyword"},
                "last_updated": {"type": "date"},
                "attachments": {
                    "type": "nested",
                    "properties": {
                        "url": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "filename": {"type": "text"},
                        "metadata": {
                            "properties": {
                                "title": {"type": "text", "analyzer": "ik_smart"},
                                "author": {"type": "text"},
                                "upload_date": {"type": "date"},
                                "file_size": {"type": "long"}
                            }
                        }
                    }
                }
            }
        }
    }
)
```

### FastAPI 后端服务

```python
# FastAPI主应用示例
from fastapi import FastAPI, Depends, HTTPException
from elasticsearch import AsyncElasticsearch
import sqlite3
import jwt
from datetime import datetime, timedelta

app = FastAPI(title="NKU Search API")

# 依赖项注入
async def get_es_client():
    es = AsyncElasticsearch(["http://localhost:9200"])
    try:
        yield es
    finally:
        await es.close()

def get_db():
    conn = sqlite3.connect("database.db")
    try:
        yield conn
    finally:
        conn.close()

# 基本搜索API
@app.get("/api/search")
async def search(
    q: str,
    page: int = 1,
    size: int = 10,
    search_type: str = "normal",
    es: AsyncElasticsearch = Depends(get_es_client)
):
    if search_type == "normal":
        query = {
            "multi_match": {
                "query": q,
                "fields": ["title^3", "content", "anchor_texts^2"]
            }
        }
    elif search_type == "phrase":
        query = {
            "match_phrase": {
                "content": q
            }
        }
    elif search_type == "wildcard":
        query = {
            "wildcard": {
                "content": q.replace("*", "\\*").replace("?", "\\?")
            }
        }

    resp = await es.search(
        index="webpages",
        body={
            "query": query,
            "from": (page - 1) * size,
            "size": size,
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {}
                }
            }
        }
    )

    return {
        "total": resp["hits"]["total"]["value"],
        "results": [
            {
                "url": hit["_source"]["url"],
                "title": hit["_source"].get("title", ""),
                "snippet": "..." + "...".join(hit.get("highlight", {}).get("content", [])[:2]) + "..." if "highlight" in hit else hit["_source"].get("content", "")[:200],
                "score": hit["_score"]
            }
            for hit in resp["hits"]["hits"]
        ]
    }
```

## 部署方法

### 开发环境运行

```bash
# 运行爬虫
cd crawler
scrapy crawl nku

# 运行后端
cd backend
uvicorn main:app --reload

# 运行前端
cd frontend
npm start
```

### 生产环境部署

#### Docker Compose 部署

创建`docker-compose.yml`:

```yaml
version: "3"

services:
    elasticsearch:
        image: elasticsearch:8.10.2
        environment:
            - discovery.type=single-node
            - xpack.security.enabled=false
        ports:
            - "9200:9200"
        volumes:
            - es_data:/usr/share/elasticsearch/data

    backend:
        build: ./backend
        ports:
            - "8000:8000"
        depends_on:
            - elasticsearch
        volumes:
            - ./data:/app/data  # SQLite数据库文件

    frontend:
        build: ./frontend
        ports:
            - "3000:80"
        depends_on:
            - backend

volumes:
    es_data:

    backend:
        build: ./backend
        ports:
            - "8000:8000"
        depends_on:
            - elasticsearch
            - mongodb

    frontend:
        build: ./frontend
        ports:
            - "3000:80"
        depends_on:
            - backend

volumes:
    es_data:
    mongo_data:
```

启动服务:

```bash
docker-compose up -d
```

## 系统监控和维护

### 日志管理

-   使用 Python 的 logging 模块记录系统日志
-   在生产环境中集成 ELK(Elasticsearch, Logstash, Kibana)进行日志分析

### 性能监控

-   使用 Prometheus 监控系统资源使用
-   使用 Grafana 创建监控面板
-   监控 Elasticsearch 集群状态和性能

### 数据备份

-   定期备份 Elasticsearch 索引
-   使用 MongoDB 的备份机制
-   存储快照到外部存储

## 扩展性和未来改进

1. **分布式爬虫**: 扩展 Scrapy 爬虫为多机分布式架构
2. **Elasticsearch 集群**: 配置 ES 集群提高性能和可靠性
3. **高级 NLP 功能**: 集成更多自然语言处理功能
4. **移动应用**: 开发移动应用版本
5. **多语言支持**: 添加英文等其他语言的支持
