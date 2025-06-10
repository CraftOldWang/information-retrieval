# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from datetime import datetime
from typing import Dict, List, Any, Optional


class WebPageItem(scrapy.Item):
    """网页数据项"""
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    html = scrapy.Field()
    anchor_texts = scrapy.Field()  # 锚文本列表
    attachments = scrapy.Field()   # 文档附件列表
    metadata = scrapy.Field()      # 元数据
    def __setitem__(self, key: str, value: Any) -> None:
        if key == 'metadata' and not value:
            # 设置默认元数据
            value = {
                'crawl_time': datetime.now().isoformat(),
                'last_modified': None,
                'content_type': 'text/html'
            }
        super().__setitem__(key, value)


class DocumentItem(scrapy.Item):
    """文档数据项（PDF、DOC等）"""
    url = scrapy.Field()
    filename = scrapy.Field()
    file_type = scrapy.Field()
    file_size = scrapy.Field()
    source_page = scrapy.Field()
    metadata = scrapy.Field()  # 包含title、author、upload_date等
    

class AnchorTextItem(scrapy.Item):
    """锚文本数据项"""
    source_url = scrapy.Field()
    target_url = scrapy.Field()
    anchor_text = scrapy.Field()
    link_context = scrapy.Field()  # 链接周围的上下文
