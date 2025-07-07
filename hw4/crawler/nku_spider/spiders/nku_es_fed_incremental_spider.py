# filepath: d:\\1Learningoutput\\Year2_Part2\\Information_Retrieval\\hw4Web_redo\\crawler\\nku_spider\\spiders\\nku_es_fed_incremental_spider.py
#
# Nankai University ES-Fed Incremental Spider
# This spider fetches a random batch of initial URLs from Elasticsearch. When it runs out of URLs to crawl,
# it connects to the `spider_idle` signal to fetch another random batch, allowing for continuous crawling
# and enabling multiple spiders to run in parallel with minimal overlap.
#

import scrapy
import re
import hashlib
from urllib.parse import urljoin, urlparse
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
from ..items import WebPageItem
from typing import Dict, List, Any, Optional, Union

# ## NEW IMPORTS ##
from scrapy import signals
from scrapy.exceptions import DontCloseSpider

import redis
import elasticsearch
# NOTE: es_scan is no longer needed for the primary fetch logic
from elasticsearch.helpers import scan as es_scan

class NkuEsFedIncrementalSpider(scrapy.Spider):
    # ## MODIFIED: New name for the spider ##
    name = "nku_es_fed_incremental"
    allowed_domains = ["nankai.edu.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
    }

    # ## NEW: Class method to handle signal connection ##
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """This method connects the spider's `spider_idle` signal to our custom handler."""
        spider = super(NkuEsFedIncrementalSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.link_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            deny=[
                r".*\.pdf$", r".*\.doc$", r".*\.docx$", r".*\.xls$", r".*\.xlsx$",
                r".*\.ppt$", r".*\.pptx$", r".*\.zip$", r".*\.rar$",
                r"/download/", r"/files/", r"/uploads/",
            ]
        )
        self.doc_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            allow=[r".*\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$"],
        )
        
        self.discovered_domains = set()
        
        # ## NEW: Attributes for incremental fetching ##
        self.es_client = None
        self.redis_client = None
        self.urls_to_crawl_batch = [] # Holds the current batch of URLs
        self.crawl_batch_size =  1000 # Target number of unique URLs per batch

        # 添加用于独立检查的正则表达式列表
        self.deny_patterns = [
            r".*\.pdf$", r".*\.doc$", r".*\.docx$", r".*\.xls$", r".*\.xlsx$",
            r".*\.ppt$", r".*\.pptx$", r".*\.zip$", r".*\.rar$",
            r"/download/", r"/files/", r"/uploads/",
        ]
        self.deny_regex = [re.compile(pattern) for pattern in self.deny_patterns]

    def _generate_url_hash(self, url: str) -> str:
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def _is_url_seen(self, url: str) -> bool:
        if not hasattr(self, 'redis_client') or self.redis_client is None:
            self.logger.warning("Redis client not available for _is_url_seen. Assuming URL not seen.")
            return False
        url_hash = self._generate_url_hash(url)
        try:
            return self.redis_client.sismember(self.crawled_urls_redis_key, url_hash)
        except redis.exceptions.RedisError as e:
            self.logger.error(f"Redis sismember failed for hash {url_hash} (URL: {url}): {e}. Assuming not seen.")
            return False

    def _is_url_denied(self, url):
        """检查URL是否应该被拒绝访问（例如，文档和下载文件）"""
        for pattern in self.deny_regex:
            if pattern.search(url):
                return True
        return False

    def start_requests(self):
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(
                host=self.settings.get("REDIS_HOST", "localhost"),
                port=self.settings.get("REDIS_PORT", 6379),
                db=self.settings.get("REDIS_DB", 0),
            )
            self.redis_client.ping()
            self.logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            self.logger.error(f"Could not connect to Redis: {e}. URL deduplication will not work.")
            self.redis_client = None

        # Initialize Elasticsearch client
        try:
            es_hosts = [{'host': self.settings.get("ELASTICSEARCH_HOST", "localhost"), 'port': self.settings.get("ELASTICSEARCH_PORT", 9200), 'scheme': self.settings.get("ELASTICSEARCH_SCHEME", "http")}]
            self.es_client = elasticsearch.Elasticsearch(es_hosts, request_timeout=30)
            if not self.es_client.ping():
                raise elasticsearch.exceptions.ConnectionError("ES ping failed")
            self.logger.info("Successfully connected to Elasticsearch.")
        except elasticsearch.exceptions.ConnectionError as e:
            self.logger.error(f"Could not connect to Elasticsearch: {e}. Cannot fetch initial URLs.")
            self.es_client = None

        self.es_index_name = self.settings.get("ELASTICSEARCH_INDEX_WEBPAGE", "nku_webpages")
        self.crawled_urls_redis_key = self.settings.get("REDIS_CRAWLED_URLS_KEY", "crawled_urls")

        # ## MODIFIED: `start_requests` now just kicks off the first fetch ##
        # It no longer yields requests directly. Instead, it populates the first batch
        # and then yields from that batch. The `spider_idle` signal handles subsequent batches.
        
        # Populate discovered_domains from fallback URLs if ES client is not available
        if not self.es_client:
            fallback_urls_for_domain_discovery = self.settings.getlist('START_URLS_FALLBACK', [])
            for url_str_fallback in fallback_urls_for_domain_discovery:
                parsed_initial_url = urlparse(url_str_fallback)
                if parsed_initial_url.netloc:
                    self.discovered_domains.add(parsed_initial_url.netloc)

        # First, try to fetch from ES.
        self.fetch_urls_from_es()

        # If ES fetch fails or returns nothing, use fallback
        if not self.urls_to_crawl_batch:
            self.logger.warning("Initial ES fetch yielded no new URLs. Trying fallback URLs.")
            fallback_urls = self.settings.getlist('START_URLS_FALLBACK', [])
            for url in fallback_urls:
                if not self._is_url_seen(url):
                    self.urls_to_crawl_batch.append(url)
            if not fallback_urls:
                 self.logger.warning("No new URLs from ES and no fallback URLs defined. Spider will close if idle.")
                 return # Nothing to do

        # Yield requests from the populated batch
        for url in self.urls_to_crawl_batch:
            yield scrapy.Request(url, self.parse)
        self.urls_to_crawl_batch.clear()

    # ## NEW METHOD ##
    def fetch_urls_from_es(self):
        """Fetches a random batch of URLs from Elasticsearch."""
        if not self.es_client:
            self.logger.warning("ES client not available. Cannot fetch new URLs.")
            return

        self.logger.info(f"Attempting to fetch a new batch of {self.crawl_batch_size} unique URLs from ES.")
        
        # We query for more documents than we need because many URLs might already be seen in Redis.
        # A 5x multiplier is a reasonable starting point.
        es_query_size = self.crawl_batch_size * 5

        # Use a function_score query with random_score to get random documents.
        # This is key for running multiple spiders in parallel without them grabbing the same work.
        query = {
            "query": {
                "function_score": {
                    "query": {"match_all": {}},
                    "functions": [{"random_score": {}}],
                    "boost_mode": "replace"
                }
            },
            "_source": ["anchor_texts"],
            "size": es_query_size
        }

        try:
            response = self.es_client.search(index=self.es_index_name, body=query)
            
            new_urls_found = set() # Use a set to handle duplicates within the ES response
            filtered_count = 0
            for hit in response['hits']['hits']:
                source = hit.get("_source", {})
                anchor_texts_data = source.get("anchor_texts", [])
                if isinstance(anchor_texts_data, list):
                    for anchor in anchor_texts_data:
                        if isinstance(anchor, dict):
                            target_url = anchor.get("href")
                            if target_url and isinstance(target_url, str) and target_url.startswith(('http://', 'https://')):
                                # 添加过滤逻辑，确保不添加被拒绝的URL
                                if not self._is_url_seen(target_url) and not self._is_url_denied(target_url):
                                    new_urls_found.add(target_url)
                                    if len(new_urls_found) >= self.crawl_batch_size:
                                        break
                                elif self._is_url_denied(target_url):
                                    filtered_count += 1
                if len(new_urls_found) >= self.crawl_batch_size:
                    break
            
            self.urls_to_crawl_batch.extend(list(new_urls_found))
            self.logger.info(f"ES Fetch Complete. Found {len(self.urls_to_crawl_batch)} new unique URLs to add to the queue. Filtered {filtered_count} denied URLs.")

        except elasticsearch.exceptions.ElasticsearchException as e:
            self.logger.error(f"Error fetching random URLs from Elasticsearch: {e}")

    # ## NEW METHOD ##
    def spider_idle(self, spider):
        """
        Handler for the spider_idle signal. Called when the spider has no more requests to process.
        """
        self.logger.info("Spider is idle. Checking for more URLs from ES.")
        
        # Fetch a new batch of URLs
        self.fetch_urls_from_es()

        # If we found new URLs, schedule them and prevent the spider from closing.
        if self.urls_to_crawl_batch:
            self.logger.info(f"Fetched {len(self.urls_to_crawl_batch)} new URLs. Scheduling them now.")
            for url_to_crawl in self.urls_to_crawl_batch:
                req = scrapy.Request(url_to_crawl, self.parse)
                # Use self.crawler.engine.crawl() to submit new requests
                if hasattr(self.crawler.engine, 'crawl'):
                    self.crawler.engine.crawl(req)
                else:
                    # Fallback or error if 'crawl' is not available, though it should be.
                    # This might indicate a very old Scrapy version or an unexpected engine state.
                    self.logger.error("self.crawler.engine.crawl method not found. Cannot schedule new requests from spider_idle.")
                    # As a last resort, you could try to add to scheduler directly, but this is less standard:
                    # self.crawler.engine.slot.scheduler.enqueue_request(req)
                    # However, this is accessing internal APIs and might break.
                    # For now, let's assume 'crawl' is the way.
            
            self.urls_to_crawl_batch.clear()
            
            # Tell Scrapy not to close yet
            raise DontCloseSpider
        else:
            self.logger.info("No new URLs found in ES. Spider will now close.")



    def parse(self, response):
        # This parse method and all helpers are unchanged from your original spider.
        # They are still responsible for processing the page and finding new links.
        self.logger.debug(f"Parsing page: {response.url}")

        item = WebPageItem()
        item["url"] = response.url
        # ... (rest of the item population is the same)
        item["title"] = self.extract_title(response)
        item["content"] = self.extract_content(response)
        item["html"] = response.text if self.settings.getbool("STORE_HTML", False) else ""
        item["anchor_texts"] = self.extract_anchor_texts(response)
        item["attachments"] = self.extract_attachments(response)
        item["metadata"] = {
            "crawl_time": datetime.now().isoformat(),
            "last_modified": self.extract_last_modified(response),
            "content_type": response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore"),
            # "status_code": response.status,
            # "depth": response.meta.get("depth", 0),
        }
        yield item

        # Continue crawling links extracted from this page
        links = self.link_extractor.extract_links(response)
        for link in links:
            if not self._is_url_seen(link.url) and not self._is_url_denied(link.url):
                parsed_link_url = urlparse(link.url)
                if parsed_link_url.netloc and any(parsed_link_url.netloc == domain or parsed_link_url.netloc.endswith("." + domain) for domain in self.allowed_domains):
                    if parsed_link_url.netloc not in self.discovered_domains:
                         self.discovered_domains.add(parsed_link_url.netloc)
                         self.logger.info(f"Discovered new subdomain while parsing: {parsed_link_url.netloc} from {link.url}")

                    # yield scrapy.Request(
                    #     url=link.url,
                    #     callback=self.parse,
                    #     meta={"depth": response.meta.get("depth", 0) + 1},
                    # )
            else:
                reason = "已经访问过" if self._is_url_seen(link.url) else "属于拒绝访问类型"
                self.logger.debug(f"跳过URL ({reason}): {link.url}")

    # --- All helper methods (extract_title, etc.) are copied directly ---
    # --- and remain unchanged. They are omitted here for brevity.    ---
    # ... (paste all your helper methods here) ...
    def extract_title(self, response) -> str:
        title = response.css("title::text").get()
        if title:
            return title.strip()
        h1_title = response.css("h1::text").get()
        if h1_title:
            return h1_title.strip()
        return "无标题"

    def extract_content(self, response) -> str:
        content_selectors = [
            "article .content", ".article-content", "div.content", ".main-content",
            ".entry-content", ".post-content", ".text", "#content", "article", "main"
        ]
        content_text = ""
        for selector in content_selectors:
            content_elements = response.css(f"{selector} ::text").getall()
            if content_elements:
                content_text = " ".join([text.strip() for text in content_elements if text.strip()])
                if len(content_text) > 100:
                    break
        if not content_text or len(content_text) < 100 :
            all_text = response.css("body ::text").getall()
            content_text = " ".join([text.strip() for text in all_text if text.strip()])
        return self.clean_text(content_text)

    def extract_anchor_texts(self, response) -> list:
        anchor_items = []
        links = response.css("a[href]")
        for link_element in links:
            href = link_element.css("::attr(href)").get()
            text_fragments = link_element.css("::text").getall()
            text = self.clean_text(" ".join(text_fragments).strip())

            if href and text:
                absolute_url = urljoin(response.url, href.strip())
                if not absolute_url.startswith(('http://', 'https://')):
                    continue
                if len(text) > 1 and len(text) < 200 and not text.lower() in ["click here", "read more", "details", "link"]:
                    anchor_items.append({"text": text, "href": absolute_url})
        return anchor_items

    def extract_attachments(self, response) -> list:
        attachments = []
        doc_links = self.doc_extractor.extract_links(response)
        for doc_link in doc_links:
            parsed_url = urlparse(doc_link.url)
            filename = parsed_url.path.split("/")[-1]
            file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"
            link_text = getattr(doc_link, "text", "")
            doc_title = self.clean_text(link_text) if link_text else filename
            
            attachments.append({
                "url": doc_link.url,
                "type": file_type,
                "filename": filename,
                "metadata": { "title": doc_title, "author": None, "upload_date": None, "file_size": None, },
            })
        return attachments

    def extract_last_modified(self, response) -> Optional[str]:
        last_modified_header = response.headers.get("Last-Modified")
        if last_modified_header:
            return last_modified_header.decode("utf-8", errors="ignore")
        
        date_patterns = [
            r"发布时间[：:]\\s*(\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?)",
            r"更新时间[：:]\\s*(\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?)",
            r"(\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?)\\s*发布",
            r"datePublished\" content=\"(\\d{4}-\\d{2}-\\d{2})\"",
            r"updated_time\" content=\"(\\d{4}-\\d{2}-\\d{2})\"",
        ]
        page_text_sample = response.text[:2048]
        for pattern in date_patterns:
            match = re.search(pattern, page_text_sample, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
                return date_str.strip()
        return None

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<script[^<]*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style[^<]*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\\s+", " ", text)
        text = re.sub(r'[^\\u4e00-\\u9fa5a-zA-Z0-9\\s\\.,;:!?()（）【】\"\"\' \"。，；：！？、·]', "", text)
        return text.strip()