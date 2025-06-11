# Elasticsearch搜索服务 - 完整实现版
import hashlib
import logging
import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from app.core.config import settings
from app.models.schemas import SearchQuery, SearchResponse, SearchResult, UserProfile

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Elasticsearch搜索服务类"""
    
    def __init__(self):
        self.es_host = settings.ELASTICSEARCH_HOST
        self.es_port = settings.ELASTICSEARCH_PORT
        self.index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_webpages"
        self.client = None
        
    async def get_client(self) -> AsyncElasticsearch:
        """获取Elasticsearch异步客户端"""
        if not self.client:
            self.client = AsyncElasticsearch(
                [f"http://{self.es_host}:{self.es_port}"],
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=30,
            )
            
            # 测试连接
            if not await self.client.ping():
                raise ConnectionError("无法连接到Elasticsearch服务")
                
        return self.client
    
    async def _build_search_query(self, query: SearchQuery, user: Optional[UserProfile] = None) -> Dict[str, Any]:
        """构建搜索查询"""
        search_text = query.query.strip()
        
        # 基础查询
        must_conditions = [
            {
                "multi_match": {
                    "query": search_text,
                    "fields": ["title^3", "content^2", "description", "keywords"],
                    "type": "best_fields",
                    "operator": "and",
                    "fuzziness": "AUTO"
                }
            }
        ]
        
        # 添加过滤条件
        filter_conditions = []
        
        # 域名过滤
        if query.domain and query.domain.strip():
            filter_conditions.append({
                "term": {"domain": query.domain.strip()}
            })
        
        # 日期范围过滤
        date_range = {}
        if query.date_from:
            date_range["gte"] = query.date_from.isoformat()
        if query.date_to:
            date_range["lte"] = query.date_to.isoformat()
            
        if date_range:
            filter_conditions.append({
                "range": {"crawl_date": date_range}
            })
        
        # 构建完整查询
        search_body = {
            "query": {
                "bool": {
                    "must": must_conditions
                }
            },
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 1, "fragment_size": 150},
                    "content": {"number_of_fragments": 2, "fragment_size": 150}
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            },
            "aggs": {
                "domains": {
                    "terms": {"field": "domain", "size": 10}
                },
                "dates": {
                    "date_histogram": {
                        "field": "crawl_date",
                        "calendar_interval": "month"
                    }
                }
            }
        }
        
        # 添加过滤条件
        if filter_conditions:
            search_body["query"]["bool"]["filter"] = filter_conditions
            
        return search_body
    
    async def _build_document_search_query(self, query: SearchQuery, doc_types: Optional[List[str]] = None, 
                                         user: Optional[UserProfile] = None) -> Dict[str, Any]:
        """构建文档搜索查询"""
        search_text = query.query.strip()
        
        # 基础查询
        must_conditions = [
            {
                "multi_match": {
                    "query": search_text,
                    "fields": ["title^3", "content^2", "description", "keywords"],
                    "type": "best_fields",
                    "operator": "and",
                    "fuzziness": "AUTO"
                }
            }
        ]
        
        # 添加文档类型过滤
        filter_conditions = []
        if doc_types and len(doc_types) > 0:
            filter_conditions.append({
                "terms": {"file_type": doc_types}
            })
        
        # 域名过滤
        if query.domain_filter and query.domain_filter:
            filter_conditions.append({
                "terms": {"domain": query.domain_filter}
            })
        
        # 日期范围过滤
        date_range = {}
        if query.date_from:
            date_range["gte"] = query.date_from.isoformat()
        if query.date_to:
            date_range["lte"] = query.date_to.isoformat()
            
        if date_range:
            filter_conditions.append({
                "range": {"crawl_date": date_range}
            })
        
        # 构建完整查询
        search_body = {
            "query": {
                "bool": {
                    "must": must_conditions
                }
            },
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 1, "fragment_size": 150},
                    "content": {"number_of_fragments": 2, "fragment_size": 150}
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            },
            "aggs": {
                "file_types": {
                    "terms": {"field": "file_type", "size": 10}
                },
                "domains": {
                    "terms": {"field": "domain", "size": 10}
                },
                "dates": {
                    "date_histogram": {
                        "field": "crawl_date",
                        "calendar_interval": "month"
                    }
                }
            }
        }
        
        # 添加过滤条件
        if filter_conditions:
            search_body["query"]["bool"]["filter"] = filter_conditions
            
        return search_body
    
    async def _process_search_results(self, response_obj: Dict[str, Any]) -> List[SearchResult]:
        """处理搜索结果"""
        results = []
        
        for hit in response_obj['hits']['hits']:
            source = hit['_source']
            
            # 处理高亮
            highlight = {}
            if 'highlight' in hit:
                highlight = hit['highlight']
            
            # 提取标题和内容的高亮片段
            title_highlight = None
            if 'title' in highlight and highlight['title']:
                title_highlight = highlight['title'][0]
                
            content_highlight = None
            if 'content' in highlight and highlight['content']:
                content_highlight = ' ... '.join(highlight['content'])
            
            # 创建搜索结果对象
            result = SearchResult(
                id=hit['_id'],
                url=source.get('url', ''),
                title=source.get('title', ''),
                description=source.get('description', ''),
                content_snippet=content_highlight or source.get('content', '')[:200],
                title_highlight=title_highlight,
                content_highlight=content_highlight,
                domain=source.get('domain', ''),
                crawl_date=source.get('crawl_date'),
                file_type=source.get('file_type', ''),
                file_size=source.get('file_size', 0),
                score=hit['_score']
            )
            
            results.append(result)
            
        return results
    
    async def _get_suggestions_from_response(self, response_obj: Dict[str, Any], query: str) -> List[str]:
        """从搜索响应中提取建议"""
        suggestions = []
        
        # 如果响应中包含建议
        if 'suggest' in response_obj:
            for suggestion_type in response_obj['suggest']:
                for suggestion in response_obj['suggest'][suggestion_type]:
                    for option in suggestion.get('options', []):
                        suggestions.append(option.get('text'))
        
        return list(set(suggestions))[:5]  # 返回去重后的前5个建议
    
    async def search(self, query: SearchQuery, user: Optional[UserProfile] = None) -> SearchResponse:
        """执行搜索查询"""
        try:
            es = await self.get_client()
            
            # 构建搜索查询
            search_body = await self._build_search_query(query, user)
            
            # 执行搜索
            response_obj = await es.search(
                index=self.index_name,
                body=search_body,
                from_=(query.page - 1) * query.page_size,
                size=query.page_size
            )
            
            # 处理搜索结果
            results = await self._process_search_results(response_obj)
            
            return SearchResponse(
                total=response_obj['hits']['total']['value'],
                page=query.page,
                page_size=query.page_size,
                results=results,
                aggregations=response_obj.get('aggregations'),
                suggestions=await self._get_suggestions_from_response(response_obj, query.query)
            )
            
        except Exception as e:
            logger.error(f"搜索执行失败: {str(e)}", exc_info=True)
            raise