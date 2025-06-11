# filepath: d:\\1Learningoutput\\Year2_Part2\\Information_Retrieval\\hw4Web_redo\\crawler\\nku_spider\\spiders\\nku_es_fed_spider.py
#
#Nankai University ES-Fed Spider
#This spider fetches initial URLs from Elasticsearch, using anchor texts of already crawled pages,
#and checks against Redis to avoid re-crawling known URLs.
#

import scrapy
import re
import hashlib
from urllib.parse import urljoin, urlparse
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
from ..items import WebPageItem # Assuming WebPageItem is the primary item
from typing import Dict, List, Any, Optional, Union

import redis
import elasticsearch
from elasticsearch.helpers import scan as es_scan

class NkuEsFedSpider(scrapy.Spider):
    name = "nku_es_fed"
    allowed_domains = ["nankai.edu.cn"]  # Base domain, includes all subdomains

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        # Ensure ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_INDEX_WEBPAGE,
        # REDIS_HOST, REDIS_PORT, REDIS_DB are defined in settings.py
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize LinkExtractors (similar to NkuMainSpider)
        self.link_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            deny=[
                r".*\.pdf$",
                r".*\.doc$",
                r".*\.docx$",
                r".*\.xls$",
                r".*\.xlsx$",
                r".*\.ppt$",
                r".*\.pptx$",
                r".*\.zip$",
                r".*\.rar$",
                r"/download/",
                r"/files/",
                r"/uploads/",
            ]
        )
        self.doc_extractor = LinkExtractor( # For identifying document attachments
            allow_domains=self.allowed_domains,
            allow=[r".*\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$"],
        )
        
        self.discovered_domains = set()
        # Client initializations and settings-dependent attributes will be handled in start_requests

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

    def start_requests(self):
        # Initialize Redis client
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host=self.settings.get("REDIS_HOST", "localhost"),
                port=self.settings.get("REDIS_PORT", 6379),
                db=self.settings.get("REDIS_DB", 0),
            )
            self.redis_client.ping()
            self.logger.info("Successfully connected to Redis in start_requests.")
        except redis.exceptions.ConnectionError as e:
            self.logger.error(f"Could not connect to Redis in start_requests: {e}. URL deduplication might not work.")
            self.redis_client = None
        except Exception as e: # Catch any other potential error during Redis init
            self.logger.error(f"An unexpected error occurred during Redis initialization in start_requests: {e}")
            self.redis_client = None

        # Initialize Elasticsearch client
        self.es_client = None
        try:
            es_hosts = [{
                'host': self.settings.get("ELASTICSEARCH_HOST", "localhost"),
                'port': self.settings.get("ELASTICSEARCH_PORT", 9200),
                'scheme': self.settings.get("ELASTICSEARCH_SCHEME", "http")
            }]
            self.es_client = elasticsearch.Elasticsearch(
                es_hosts,
                request_timeout=self.settings.get("ELASTICSEARCH_REQUEST_TIMEOUT", 30)
            )
            if not self.es_client.ping():
                raise elasticsearch.exceptions.ConnectionError("ES ping failed in start_requests")
            self.logger.info("Successfully connected to Elasticsearch in start_requests.")
        except elasticsearch.exceptions.ConnectionError as e:
            self.logger.error(f"Could not connect to Elasticsearch in start_requests: {e}. Cannot fetch initial URLs from ES.")
            self.es_client = None
        except Exception as e: # Catch any other potential error during ES init
            self.logger.error(f"An unexpected error occurred during Elasticsearch initialization in start_requests: {e}")
            self.es_client = None
        
        self.es_index_name = self.settings.get("ELASTICSEARCH_INDEX_WEBPAGE", "nku_webpages")
        self.crawled_urls_redis_key = self.settings.get("REDIS_CRAWLED_URLS_KEY", "crawled_urls")

        # Populate discovered_domains from fallback URLs if ES client is not available
        # This is done here because self.settings is now reliably available.
        if not self.es_client:
            fallback_urls_for_domain_discovery = self.settings.getlist('START_URLS_FALLBACK', [])
            for url_str_fallback in fallback_urls_for_domain_discovery:
                parsed_initial_url = urlparse(url_str_fallback)
                if parsed_initial_url.netloc:
                    self.discovered_domains.add(parsed_initial_url.netloc)


        if not self.es_client:
            self.logger.error("Elasticsearch client not initialized. Attempting to use fallback URLs.")
            # Fallback to default start_urls from settings if ES is unavailable
            fallback_urls = self.settings.getlist('START_URLS_FALLBACK', [])
            if not fallback_urls:
                 self.logger.warning("No fallback START_URLS_FALLBACK defined in settings.")
                 return

            self.logger.info(f"Falling back to START_URLS_FALLBACK: {fallback_urls}")
            for url in fallback_urls:
                if not self._is_url_seen(url):
                    yield scrapy.Request(url, self.parse)
                else:
                    self.logger.info(f"Fallback URL already seen in Redis: {url}")
            return

        initial_urls_to_crawl = set()
        processed_anchor_hrefs_count = 0
        es_page_size = self.settings.getint("ES_SCROLL_SIZE", 100)
        es_scroll_time = self.settings.get("ES_SCROLL_TIME", "5m")

        self.logger.info(f"Starting to fetch initial URLs from Elasticsearch index '{self.es_index_name}'")

        try:
            query = {
                "query": {"match_all": {}},
                "_source": ["url", "anchor_texts"] # Fetching document URL and its anchor_texts array
            }

            for hit in es_scan(self.es_client, index=self.es_index_name, query=query, scroll=es_scroll_time, size=es_page_size):
                source = hit.get("_source", {})
                
                # User stated: "只有anchor_texts 里的href 对应的链接才可能没爬过"
                # So we primarily focus on these.
                anchor_texts_data = source.get("anchor_texts", [])
                if isinstance(anchor_texts_data, list):
                    for anchor in anchor_texts_data:
                        if isinstance(anchor, dict):
                            target_url = anchor.get("href")
                            if target_url and isinstance(target_url, str) and target_url.startswith(('http://', 'https://')):
                                if not self._is_url_seen(target_url):
                                    initial_urls_to_crawl.add(target_url)
                                processed_anchor_hrefs_count += 1
                
                if processed_anchor_hrefs_count > 0 and processed_anchor_hrefs_count % (es_page_size * 10) == 0:
                    self.logger.info(f"Processed {processed_anchor_hrefs_count} anchor hrefs from ES. Unique URLs to crawl so far: {len(initial_urls_to_crawl)}")

        except elasticsearch.exceptions.ElasticsearchException as e:
            self.logger.error(f"Error fetching URLs from Elasticsearch using scan: {e}")
            # Potentially use fallback URLs here too if ES scan fails mid-way

        self.logger.info(f"Finished fetching from ES. Total unique URLs to potentially crawl: {len(initial_urls_to_crawl)}")
        
        if not initial_urls_to_crawl:
            self.logger.warning("No new initial URLs found from ES to crawl.")
            # Consider a small seed list from settings if this often happens and is undesirable
            # For now, if ES yields nothing new, and no fallback was triggered, it will stop if this set is empty.

        for url_to_crawl in initial_urls_to_crawl:
            # Update discovered_domains (for logging or other logic)
            parsed_url_obj = urlparse(url_to_crawl)
            if parsed_url_obj.netloc:
                is_allowed = any(parsed_url_obj.netloc == domain or parsed_url_obj.netloc.endswith("." + domain) for domain in self.allowed_domains)
                if is_allowed and parsed_url_obj.netloc not in self.discovered_domains:
                     self.discovered_domains.add(parsed_url_obj.netloc)
                     self.logger.info(f"Discovered new subdomain from ES source to crawl: {parsed_url_obj.netloc}")
            
            # Scrapy's OffsiteMiddleware will filter based on allowed_domains if active.
            # We've already filtered by _is_url_seen.
            yield scrapy.Request(url_to_crawl, self.parse)

    def parse(self, response):
        self.logger.debug(f"Parsing page: {response.url}")

        item = WebPageItem()
        item["url"] = response.url
        item["title"] = self.extract_title(response)
        item["content"] = self.extract_content(response)
        item["html"] = response.text if self.settings.getbool("STORE_HTML", False) else ""
        
        # Extract anchor texts and attachments using copied methods
        # These methods internally handle URL joining and cleaning
        item["anchor_texts"] = self.extract_anchor_texts(response)
        item["attachments"] = self.extract_attachments(response)
        
        item["metadata"] = {
            "crawl_time": datetime.now().isoformat(),
            "last_modified": self.extract_last_modified(response),
            "content_type": response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore"),
            "status_code": response.status,
            "depth": response.meta.get("depth", 0),
        }
        yield item

        # Continue crawling links extracted from this page
        links = self.link_extractor.extract_links(response)
        for link in links:
            if not self._is_url_seen(link.url):
                parsed_link_url = urlparse(link.url)
                if parsed_link_url.netloc and any(parsed_link_url.netloc == domain or parsed_link_url.netloc.endswith("." + domain) for domain in self.allowed_domains):
                    if parsed_link_url.netloc not in self.discovered_domains:
                         self.discovered_domains.add(parsed_link_url.netloc)
                         self.logger.info(f"Discovered new subdomain while parsing: {parsed_link_url.netloc} from {link.url}")

                    yield scrapy.Request(
                        url=link.url,
                        callback=self.parse,
                        meta={"depth": response.meta.get("depth", 0) + 1},
                    )
                # else: # Log if link is off-domain, though OffsiteMiddleware handles this
                #    self.logger.debug(f"Skipping off-domain link: {link.url}")
            else:
                self.logger.debug(f"Skipping already seen URL from page {response.url}: {link.url}")

    # --- Helper methods copied from NkuMainSpider ---
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
                if len(content_text) > 100: # Basic check for meaningful content
                    break
        if not content_text or len(content_text) < 100 : # Fallback if specific selectors fail or yield too little
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
                # Filter out non-http/https URLs early
                if not absolute_url.startswith(('http://', 'https://')):
                    continue
                # Filter out very short or generic anchor texts
                if len(text) > 1 and len(text) < 200 and not text.lower() in ["click here", "read more", "details", "link"]:
                    anchor_items.append({"text": text, "href": absolute_url})
        return anchor_items

    def extract_attachments(self, response) -> list:
        attachments = []
        doc_links = self.doc_extractor.extract_links(response) # Uses the specific doc LinkExtractor
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
                "metadata": {
                    "title": doc_title,
                    "author": None,  # 无法从HTML中获取
                    "upload_date": None,  # 无法从HTML中获取
                    "file_size": None,  # 需要额外请求才能获取
                },
            })
        return attachments

    def extract_last_modified(self, response) -> Optional[str]:
        last_modified_header = response.headers.get("Last-Modified")
        if last_modified_header:
            return last_modified_header.decode("utf-8", errors="ignore")
        
        # Common patterns in HTML content
        date_patterns = [
            r"发布时间[：:]\\s*(\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?)",
            r"更新时间[：:]\\s*(\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?)",
            r"(\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?)\\s*发布",
            r"datePublished\" content=\"(\\d{4}-\\d{2}-\\d{2})\"",
            r"updated_time\" content=\"(\\d{4}-\\d{2}-\\d{2})\"",
        ]
        page_text_sample = response.text[:2048] # Search in a sample to avoid large regex on full body
        for pattern in date_patterns:
            match = re.search(pattern, page_text_sample, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Basic normalization attempt (can be expanded)
                date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
                return date_str.strip()
        return None

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<script[^<]*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style[^<]*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text) # Remove all other HTML tags, replace with space
        text = re.sub(r"\\s+", " ", text) # Normalize whitespace
        # Consider more aggressive cleaning for specific unwanted characters if needed
        text = re.sub(r'[^\\u4e00-\\u9fa5a-zA-Z0-9\\s\\.,;:!?()（）【】\"\"\' \"。，；：！？、·]', "", text) # Example from old spider
        return text.strip()

