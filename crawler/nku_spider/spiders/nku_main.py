"""
南开大学主站爬虫
爬取南开大学官方网站的网页内容
"""

import scrapy
import re
from urllib.parse import urljoin, urlparse
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
from ..items import WebPageItem, AnchorTextItem, DocumentItem


class NkuMainSpider(scrapy.Spider):
    name = "nku_main"
    allowed_domains = ["nankai.edu.cn", "www.nankai.edu.cn"]
    start_urls = [
        # 主站及核心站点
        "https://www.nankai.edu.cn",
        "https://news.nankai.edu.cn",
        # "https://english.nankai.edu.cn",
        
        # 院系网站
        "https://wxy.nankai.edu.cn",
        "https://history.nankai.edu.cn",
        "https://phil.nankai.edu.cn",
        "https://law.nankai.edu.cn",
        "https://zfxy.nankai.edu.cn",
        "https://economics.nankai.edu.cn",
        "https://business.nankai.edu.cn",
        "https://math.nankai.edu.cn",
        "https://physics.nankai.edu.cn",
        "https://chem.nankai.edu.cn",
        "https://sky.nankai.edu.cn",
        "https://medical.nankai.edu.cn",
        
        # 职能部门
        "https://jwc.nankai.edu.cn",
        # "https://gs.nankai.edu.cn",
        # "https://kjc.nankai.edu.cn",
        # "https://xsc.nankai.edu.cn",
        "https://international.nankai.edu.cn",
        
        # 其他重要站点
        "https://lib.nankai.edu.cn",
        "https://career.nankai.edu.cn",
        "https://zsb.nankai.edu.cn",
        # "https://xyh.nankai.edu.cn",
        # "https://mooc.nankai.edu.cn"
    ]   

    # 自定义设置
    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            ],
            restrict_text=["更多", "详情", "查看", "阅读", "进入", "点击"],
        )

        # 文档链接提取器
        self.doc_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            allow=[r".*\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$"],
        )

    def parse(self, response):
        """解析页面内容"""
        self.logger.info(f"正在解析页面: {response.url}")

        # 提取页面基本信息
        item = WebPageItem()
        item["url"] = response.url
        item["title"] = self.extract_title(response)
        item["content"] = self.extract_content(response)
        item["html"] = response.text
        item["anchor_texts"] = []
        item["attachments"] = []
        item["metadata"] = {
            "crawl_time": datetime.now().isoformat(),
            "last_modified": self.extract_last_modified(response),
            "content_type": response.headers.get("Content-Type", "").decode(
                "utf-8", errors="ignore"
            ),
        }

        # 提取锚文本
        anchor_texts = self.extract_anchor_texts(response)
        item["anchor_texts"] = anchor_texts

        # 提取文档附件信息
        attachments = self.extract_attachments(response)
        item["attachments"] = attachments

        yield item

        # 继续爬取链接
        links = self.link_extractor.extract_links(response)
        for link in links:
            yield scrapy.Request(
                url=link.url,
                callback=self.parse,
                meta={"depth": response.meta.get("depth", 0) + 1},
            )

    def extract_title(self, response):
        """提取页面标题"""
        title = response.css("title::text").get()
        if title:
            return title.strip()

        # 备选方案
        h1_title = response.css("h1::text").get()
        if h1_title:
            return h1_title.strip()

        return "无标题"

    def extract_content(self, response):
        """提取页面正文内容"""
        # 尝试多种选择器提取正文
        content_selectors = [
            ".main-content",
            ".content",
            ".article-content",
            ".news-content",
            ".page-content",
            "main",
            ".container",
        ]

        content_text = ""

        for selector in content_selectors:
            content_elements = response.css(f"{selector} *::text").getall()
            if content_elements:
                content_text = " ".join(
                    [text.strip() for text in content_elements if text.strip()]
                )
                break

        # 如果没有找到特定的内容区域，提取body中的文本
        if not content_text:
            all_text = response.css("body *::text").getall()
            content_text = " ".join([text.strip() for text in all_text if text.strip()])

        # 清理文本
        content_text = self.clean_text(content_text)

        return content_text

    def extract_anchor_texts(self, response):
        """提取页面中的锚文本"""
        anchor_texts = []

        # 提取所有链接
        links = response.css("a[href]")
        for link in links:
            href = link.css("::attr(href)").get()
            text = link.css("::text").get()

            if href and text:
                # 转换为绝对URL
                absolute_url = urljoin(response.url, href)

                # 清理锚文本
                cleaned_text = self.clean_text(text)

                if cleaned_text and len(cleaned_text) > 1:
                    anchor_texts.append({"text": cleaned_text, "href": absolute_url})

        return anchor_texts

    def extract_attachments(self, response):
        """提取文档附件信息"""
        attachments = []

        # 查找文档链接
        doc_links = self.doc_extractor.extract_links(response)

        for link in doc_links:
            # 解析文件信息
            parsed_url = urlparse(link.url)
            filename = parsed_url.path.split("/")[-1]
            file_type = (
                filename.split(".")[-1].lower() if "." in filename else "unknown"
            )

            # 尝试从链接文本中提取文档标题
            link_text = getattr(link, "text", "")
            doc_title = self.clean_text(link_text) if link_text else filename

            attachment = {
                "url": link.url,
                "type": file_type,
                "filename": filename,
                "metadata": {
                    "title": doc_title,
                    "author": None,  # 无法从HTML中获取
                    "upload_date": None,  # 无法从HTML中获取
                    "file_size": None,  # 需要额外请求才能获取
                },
            }

            attachments.append(attachment)

        return attachments

    def extract_last_modified(self, response):
        """提取页面最后修改时间"""
        # 尝试从HTTP头中获取
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            return last_modified.decode("utf-8", errors="ignore")

        # 尝试从页面内容中提取
        date_patterns = [
            r"发布时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
            r"更新时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
            r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)\s*发布",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)

        return None

    def clean_text(self, text):
        """清理文本内容"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r"\s+", " ", text)

        # 移除特殊字符，但保留中文标点
        text = re.sub(
            r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,;:!?()（）【】""' "。，；：！？、·]",
            "",
            text,
        )

        return text.strip()
