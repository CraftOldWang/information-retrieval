# Scrapy settings for nku_spider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "nku_spider"

SPIDER_MODULES = ["nku_spider.spiders"]
NEWSPIDER_MODULE = "nku_spider.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#     "nku_spider.middlewares.NkuSpiderSpiderMiddleware": 543,
# }

# 临时禁用自定义Spider中间件，避免异步兼容性问题
SPIDER_MIDDLEWARES = {}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "nku_spider.middlewares.NkuSpiderDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
}

# Configure pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "nku_spider.pipelines.DataCleaningPipeline": 300,
    "nku_spider.pipelines.DuplicatesPipeline": 400,
    "nku_spider.pipelines.ElasticsearchPipeline": 500,
    "nku_spider.pipelines.FilePipeline": 600,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Redis配置 (用于分布式爬虫)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# 添加以下配置以启用Redis分布式爬虫
# 注释掉这些行可以切换回普通模式
# Redis分布式爬虫设置
# SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# SCHEDULER_PERSIST = True  # 保持爬取状态
# SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderPriorityQueue"
# REDIS_START_URLS_AS_SET = False  # 使用列表而不是集合存储起始URL

# Elasticsearch配置
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200

# 文件存储路径
DATA_PATH = "../data/raw"
SNAPSHOT_PATH = "../data/snapshots"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "../data/logs/scrapy.log"

# 自定义设置
DEPTH_LIMIT = 5  # 爬取深度限制
DEPTH_PRIORITY = 1  # 深度优先

# 允许爬取的域名
ALLOWED_DOMAINS = [
    "nankai.edu.cn",  # 这样配置会包含所有nankai.edu.cn的子域名
]

# 爬虫限制设置
CLOSESPIDER_ITEMCOUNT = 1000000  # 最大爬取项目数量
CLOSESPIDER_TIMEOUT = 0  # 不设置超时，便于长时间爬取
DEPTH_LIMIT = 10  # 设置爬取深度限制，避免无限递归

# 文件存储配置
FILES_STORE = 'data/documents'
# 不下载特大文件
DOWNLOAD_MAXSIZE = 20 * 1024 * 1024  # 20MB

# 网络连接优化设置
ROBOTSTXT_OBEY = True
ROBOTSTXT_USER_AGENT = "*"
# 对于robots.txt获取失败的情况，设置更宽松的策略
ROBOTSTXT_USE_CACHE = True
ROBOTSTXT_CACHE_SIZE = 500

# 爬取超时设置
DOWNLOAD_TIMEOUT = 7

# 重试设置
RETRY_TIMES = 0
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# DNS超时
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60
