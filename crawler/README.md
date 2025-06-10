# NKU 搜索引擎爬虫模块实现文档

## 🕷️ 模块概述

本爬虫模块基于 Scrapy 框架开发，专门用于抓取南开大学官网及相关站点的网页内容。整个模块采用模块化设计，包含数据项定义、爬虫逻辑、数据处理管道、中间件和配置管理等组件。

## 📁 文件结构

```
crawler/
├── scrapy.cfg              # Scrapy项目配置文件
└── nku_spider/             # 爬虫包
    ├── __init__.py         # 包初始化文件
    ├── items.py            # 数据项定义
    ├── middlewares.py      # 中间件
    ├── pipelines.py        # 数据处理管道
    ├── settings.py         # 爬虫设置
    └── spiders/            # 爬虫目录
        ├── __init__.py     # 包初始化文件
        └── nku_main.py     # 主爬虫
```

## 🎯 核心组件详解

### 1. 数据项定义 (`items.py`)

定义了三种数据结构来存储不同类型的爬取数据：

#### WebPageItem - 网页数据项

```python
class WebPageItem(scrapy.Item):
    url = scrapy.Field()            # 页面URL
    title = scrapy.Field()          # 页面标题
    content = scrapy.Field()        # 正文内容
    html = scrapy.Field()           # 原始HTML代码
    anchor_texts = scrapy.Field()   # 锚文本列表
    attachments = scrapy.Field()    # 附件信息列表
    metadata = scrapy.Field()       # 元数据（爬取时间、修改时间等）
```

**作用**: 标准化网页数据格式，确保数据结构一致性。

#### DocumentItem - 文档数据项

```python
class DocumentItem(scrapy.Item):
    url = scrapy.Field()            # 文档URL
    filename = scrapy.Field()       # 文件名
    file_type = scrapy.Field()      # 文件类型（pdf、doc等）
    file_size = scrapy.Field()      # 文件大小
    source_page = scrapy.Field()    # 来源页面
    metadata = scrapy.Field()       # 文档元数据
```

**作用**: 存储 PDF、DOC 等文档的元信息，不下载文档内容。

#### AnchorTextItem - 锚文本数据项

```python
class AnchorTextItem(scrapy.Item):
    source_url = scrapy.Field()     # 源页面URL
    target_url = scrapy.Field()     # 目标页面URL
    anchor_text = scrapy.Field()    # 锚文本内容
    link_context = scrapy.Field()   # 链接上下文
```

**作用**: 专门存储页面间的链接关系，用于后续的 PageRank 计算。

### 2. 主爬虫 (`nku_main.py`)

#### 爬虫配置

```python
name = "nku_main"
allowed_domains = ["nankai.edu.cn", "www.nankai.edu.cn"]
start_urls = [
    "https://www.nankai.edu.cn/",
    "https://www.nankai.edu.cn/about/",
    # ... 更多起始URL
]
```

**设计思路**:

-   限定爬取域名，确保只抓取南开相关内容
-   多个起始 URL 提高覆盖率
-   使用 LinkExtractor 自动发现新链接

#### 核心方法解析

**`parse(self, response)` - 主解析方法**

```python
def parse(self, response):
    # 1. 提取页面基本信息
    item = WebPageItem()
    item["url"] = response.url
    item["title"] = self.extract_title(response)
    item["content"] = self.extract_content(response)

    # 2. 提取锚文本和附件
    item["anchor_texts"] = self.extract_anchor_texts(response)
    item["attachments"] = self.extract_attachments(response)

    # 3. 继续爬取发现的链接
    links = self.link_extractor.extract_links(response)
    for link in links:
        yield scrapy.Request(url=link.url, callback=self.parse)

    yield item
```

**`extract_content(self, response)` - 内容提取**

```python
def extract_content(self, response):
    # 尝试多种选择器提取正文
    content_selectors = [
        ".main-content", ".content", ".article-content",
        ".news-content", ".page-content", "main", ".container"
    ]

    for selector in content_selectors:
        content_elements = response.css(f"{selector} *::text").getall()
        if content_elements:
            content_text = " ".join([text.strip() for text in content_elements])
            break

    return self.clean_text(content_text)
```

**设计亮点**:

-   **多选择器策略**: 适应不同页面结构
-   **回退机制**: 确保总能提取到内容
-   **智能清洗**: 去除无用字符和空白

### 3. 数据处理管道 (`pipelines.py`)

采用管道式数据处理，每个管道负责特定功能：

#### DataCleaningPipeline - 数据清洗管道

```python
class DataCleaningPipeline:
    def process_item(self, item, spider):
        if "content" in item:
            item["content"] = self.clean_html_content(item["content"])
            item["content"] = self.clean_text(item["content"])
        return item
```

**功能**:

-   移除 HTML 标签和脚本
-   清理特殊字符
-   统一空白字符
-   初始化 jieba 分词器

#### DuplicatesPipeline - 去重管道

```python
class DuplicatesPipeline:
    def process_item(self, item, spider):
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()

        if self.is_duplicate(url_hash, spider):
            raise DropItem(f"重复URL: {url}")

        self.mark_processed(url_hash, spider)
        return item
```

**功能**:

-   **分布式去重**: 支持 Redis 集群
-   **本地备份**: Redis 失败时使用内存
-   **哈希优化**: MD5 减少内存占用

#### ElasticsearchPipeline - 搜索索引管道

```python
class ElasticsearchPipeline:
    def create_indices(self, spider):
        webpage_mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "ik_max_word"},
                    "content": {"type": "text", "analyzer": "ik_max_word"},
                    "domain": {"type": "keyword"},
                    # ... 更多字段
                }
            }
        }
```

**功能**:

-   **智能索引**: 使用 IK 中文分词器
-   **嵌套文档**: 支持附件等复杂数据
-   **自动优化**: 设置分片和副本策略

#### FilePipeline - 文件存储管道

```python
class FilePipeline:
    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
```

**功能**:

-   **JSONL 格式**: 便于数据分析
-   **按日期分文件**: 便于管理
-   **增量写入**: 支持断点续传

### 4. 爬虫设置 (`settings.py`)

#### 性能配置

```python
CONCURRENT_REQUESTS = 16          # 并发请求数
DOWNLOAD_DELAY = 2               # 请求间隔
AUTOTHROTTLE_ENABLED = True      # 自动限速
HTTPCACHE_ENABLED = True         # HTTP缓存
```

#### 礼貌爬取

```python
ROBOTSTXT_OBEY = True            # 遵守robots.txt
USER_AGENT = "Mozilla/5.0..."    # 真实浏览器标识
```

#### 管道配置

```python
ITEM_PIPELINES = {
    "nku_spider.pipelines.DataCleaningPipeline": 300,
    "nku_spider.pipelines.DuplicatesPipeline": 400,
    "nku_spider.pipelines.ElasticsearchPipeline": 500,
}
```

## 🔍 代码问题检查

在检查代码过程中，我发现了几个需要修正的问题：

### 问题 1: Elasticsearch 索引方法过时

**位置**: `pipelines.py` 第 264 行

```python
# 问题代码
result = es.index(index=index_name, body=test_doc)

# 应该改为
result = es.index(index=index_name, document=test_doc)
```

### 问题 2: 管道配置缺少 FilePipeline

**位置**: `settings.py` 管道配置

```python
# 当前配置缺少FilePipeline
ITEM_PIPELINES = {
    "nku_spider.pipelines.DataCleaningPipeline": 300,
    "nku_spider.pipelines.DuplicatesPipeline": 400,
    "nku_spider.pipelines.ElasticsearchPipeline": 500,
    # 缺少 FilePipeline
}
```

### 问题 3: Elasticsearch 连接配置需要更新

**位置**: `pipelines.py` ElasticsearchPipeline

```python
# 需要更新为新版本的连接方式
self.es = Elasticsearch(
    ["http://localhost:9200"],
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=30
)
```

## 🎯 设计评估

### 优点分析

1. **模块化设计**: 各组件职责清晰，易于维护
2. **容错机制**: 多种备选方案确保稳定性
3. **性能优化**: 并发、缓存、限速等机制
4. **数据质量**: 多层清洗和去重保证

### 可能的复杂化问题

1. **过多的数据项类型**: `DocumentItem`和`AnchorTextItem`可能用不到
2. **管道过多**: 可以考虑合并一些简单管道
3. **配置过于详细**: 某些配置可以使用默认值

### 简化建议

1. **合并数据项**: 将所有数据统一到`WebPageItem`中
2. **简化管道**: 合并清洗和去重管道
3. **减少配置**: 去除不必要的自定义配置

## 🚀 使用方法

### 1. 启动爬虫

```bash
cd crawler
scrapy crawl nku_main
```

### 2. 限制爬取数量（测试用）

```bash
scrapy crawl nku_main -s CLOSESPIDER_ITEMCOUNT=100
```

### 3. 查看爬取统计

```bash
scrapy crawl nku_main -s LOG_LEVEL=INFO
```

## 📊 预期效果

-   **爬取速度**: 每小时约 1000-2000 个页面
-   **数据质量**: 自动去重，文本清洗
-   **存储格式**: Elasticsearch 索引 + JSONL 备份
-   **内存占用**: 分布式去重减少内存压力

## 🔧 后续优化方向

1. **增量爬取**: 定期更新已爬取页面
2. **智能调度**: 根据页面重要性调整优先级
3. **内容分析**: 添加关键词提取和摘要生成
4. **监控系统**: 添加爬取状态监控和报警

这个爬虫设计在功能完整性和实现复杂度之间取得了较好的平衡，既能满足 10 万+页面的爬取需求，又保持了代码的可维护性。
