# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import os
import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Optional, Union
import jieba
from scrapy.exceptions import DropItem
from scrapy import Spider
from scrapy.http import Response
from elasticsearch import Elasticsearch
import redis


class DataCleaningPipeline:
    """数据清洗管道"""

    def __init__(self) -> None:
        # 初始化jieba分词器
        jieba.initialize()

    def process_item(self, item: Dict[str, Any], spider: Spider) -> Dict[str, Any]:
        if "content" in item:
            # 清洗HTML内容
            item["content"] = self.clean_html_content(item["content"])
            # 提取并清洗文本
            item["content"] = self.clean_text(item["content"])

        if "title" in item:
            item["title"] = self.clean_text(item["title"])

        return item

    def clean_html_content(self, html_content):
        """清洗HTML内容"""
        if not html_content:
            return ""

        # 移除script和style标签
        html_content = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html_content = re.sub(
            r"<style[^>]*>.*?</style>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # 移除HTML标签
        html_content = re.sub(r"<[^>]+>", "", html_content)

        # 移除多余的空白字符
        html_content = re.sub(r"\s+", " ", html_content)

        return html_content.strip()

    def clean_text(self, text):
        """清洗文本内容"""
        if not text:
            return ""

        # 移除特殊字符，保留中文、英文、数字和常用标点
        text = re.sub(
            r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,;:!?()（）【】""' "。，；：！？]", "", text
        )

        # 移除多余空白
        text = re.sub(r"\s+", " ", text)

        return text.strip()


class DuplicatesPipeline:
    """去重管道"""

    def __init__(self):
        self.seen_urls = set()
        self.redis_client = None

    def open_spider(self, spider):
        try:
            # 连接Redis用于分布式去重
            self.redis_client = redis.Redis(
                host=spider.settings.get("REDIS_HOST", "localhost"),
                port=spider.settings.get("REDIS_PORT", 6379),
                db=spider.settings.get("REDIS_DB", 0),
                decode_responses=True,
            )
        except Exception as e:
            spider.logger.warning(f"Redis连接失败，使用本地去重: {e}")
            self.redis_client = None

    def process_item(self, item, spider):
        url = item.get("url")
        if not url:
            raise DropItem("缺少URL字段")

        # 生成URL的哈希值
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()

        # 检查是否重复
        if self.is_duplicate(url_hash, spider):
            raise DropItem(f"重复URL: {url}")

        # 标记为已处理
        self.mark_processed(url_hash, spider)

        return item

    def is_duplicate(self, url_hash, spider):
        """检查URL是否重复"""
        if self.redis_client:
            try:
                return self.redis_client.sismember("crawled_urls", url_hash)
            except Exception as e:
                spider.logger.warning(f"Redis检查失败: {e}")

        return url_hash in self.seen_urls

    def mark_processed(self, url_hash, spider):
        """标记URL为已处理"""
        if self.redis_client:
            try:
                self.redis_client.sadd("crawled_urls", url_hash)
                return
            except Exception as e:
                spider.logger.warning(f"Redis标记失败: {e}")

        self.seen_urls.add(url_hash)


class ElasticsearchPipeline:
    """Elasticsearch存储管道"""

    def __init__(self, elasticsearch_host: str, elasticsearch_port: int):
        self.elasticsearch_host = elasticsearch_host
        self.elasticsearch_port = elasticsearch_port
        self.es: Optional[Elasticsearch] = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            elasticsearch_host=crawler.settings.get("ELASTICSEARCH_HOST", "localhost"),
            elasticsearch_port=crawler.settings.get("ELASTICSEARCH_PORT", 9200),
        )

    def open_spider(self, spider):
        try:
            self.es = Elasticsearch(
                [f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"],
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=30,
            )

            # 检查连接
            if self.es.ping():
                spider.logger.info("Elasticsearch连接成功")
                # 创建索引
                self.create_indices(spider)
            else:
                spider.logger.error("Elasticsearch连接失败")

        except Exception as e:
            spider.logger.error(f"Elasticsearch初始化失败: {e}")

    def create_indices(self, spider):
        """创建索引"""
        if not self.es:
            spider.logger.error("Elasticsearch客户端未初始化，无法创建索引")
            return
        # 网页索引配置
        webpage_mapping = {
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "default",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "content": {"type": "text", "analyzer": "default"},
                    "html": {"type": "text", "store": True},  # 存储HTML
                    "anchor_texts": {
                        "type": "nested",  # 嵌套类型
                        "properties": {
                            "text": {"type": "text", "analyzer": "default"},
                            "href": {"type": "keyword"}
                        }
                    },
                    "domain": {"type": "keyword"},
                    "metadata": {
                        "properties": {
                            "crawl_time": {"type": "date"},
                            "last_modified": {"type": "date"},
                            "content_type": {"type": "keyword"},
                        }
                    },
                    "attachments": {
                        "type": "nested",
                        "properties": {
                            "url": {"type": "keyword"},
                            "filename": {
                                "type": "text",
                                "fields": {"keyword": {"type": "keyword"}},
                            },
                            "type": {"type": "keyword"},
                            "metadata": {
                                "properties": {
                                    "title": {"type": "text", "analyzer": "default"},
                                    "author": {"type": "text"},
                                    "upload_date": {"type": "date"},
                                    "file_size": {"type": "long"},
                                }
                            },
                        },
                    },
                }
            },
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "default": {"type": "custom", "tokenizer": "ik_smart"}
                    }
                },
            },
        }

        try:
            # 创建网页索引
            if not self.es.indices.exists(index="nku_webpages"):
                self.es.indices.create(index="nku_webpages", body=webpage_mapping)
                spider.logger.info("创建网页索引成功")

        except Exception as e:
            spider.logger.error(f"创建索引失败: {e}")

    def process_item(self, item, spider):
        if not self.es:
            return item

        try:
            # 准备文档数据
            doc = dict(item)

            # 添加域名信息
            if "url" in doc:
                parsed_url = urlparse(doc["url"])
                doc["domain"] = parsed_url.netloc

            # 生成文档ID
            doc_id = hashlib.md5(doc["url"].encode("utf-8")).hexdigest()

            # 索引到Elasticsearch
            self.es.index(index="nku_webpages", id=doc_id, document=doc)

            spider.logger.debug(f"文档已索引: {doc['url']}")

        except Exception as e:
            spider.logger.error(f"索引文档失败: {e}")

        return item

    def close_spider(self, spider):
        if self.es:
            try:
                # 刷新索引
                self.es.indices.refresh(index="nku_webpages")
                spider.logger.info("索引刷新完成")
            except Exception as e:
                spider.logger.error(f"刷新索引失败: {e}")


class FilePipeline:
    """文件存储管道"""

    def __init__(self, data_path: str):
        self.data_path = data_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(data_path=crawler.settings.get("DATA_PATH", "../data/raw"))

    def open_spider(self, spider):
        # 确保数据目录存在
        os.makedirs(self.data_path, exist_ok=True)

        # 创建以日期命名的文件
        today = datetime.now().strftime("%Y-%m-%d")
        self.file_path = os.path.join(self.data_path, f"crawled_data_{today}.jsonl")
        self.file = open(self.file_path, "a", encoding="utf-8")

    def process_item(self, item, spider):
        # 将数据写入JSONL文件
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item

    def close_spider(self, spider):
        self.file.close()
