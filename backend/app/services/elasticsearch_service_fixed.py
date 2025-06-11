# Elasticsearch搜索服务 - 修复版
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
    
    async def search_documents(self, query: SearchQuery, doc_types: Optional[List[str]] = None, 
                             user: Optional[UserProfile] = None) -> SearchResponse:
        """执行文档搜索"""
        try:
            es = await self.get_client()
            
            # 构建文档搜索查询
            search_body = await self._build_document_search_query(query, doc_types, user)
            
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
                aggregations=response_obj.get('aggregations')
            )
            
        except Exception as e:
            logger.error(f"文档搜索执行失败: {str(e)}", exc_info=True)
            raise
    
    async def personalized_search(self, query: SearchQuery, user: UserProfile) -> SearchResponse:
        """执行个性化搜索，根据用户历史行为和偏好调整结果"""
        try:
            # 先执行基础搜索
            basic_results = await self.search(query, user=None)
            
            # 如果用户已登录，应用个性化排序
            if user:
                # 获取用户偏好
                user_preferences = await self._get_user_preferences(user.id)
                
                # 应用个性化重排序
                results = await self._apply_personalization(basic_results, user, query)
                
                # 记录搜索历史
                await self.record_search_history(user.id, query, results.total)
                
                return results
            else:
                # 未登录用户返回基础搜索结果
                return basic_results
                
        except Exception as e:
            logger.error(f"个性化搜索执行失败: {str(e)}", exc_info=True)
            raise
    
    async def get_suggestions(self, query: str, limit: int, user: Optional[UserProfile] = None) -> List[str]:
        """获取搜索建议"""
        try:
            es = await self.get_client()
            
            # 构建建议查询
            suggest_body = {
                "suggest": {
                    "text": query,
                    "simple_phrase": {
                        "phrase": {
                            "field": "title.keyword",
                            "size": limit,
                            "gram_size": 2,
                            "direct_generator": [{
                                "field": "title.keyword",
                                "suggest_mode": "always"
                            }]
                        }
                    },
                    "completion": {
                        "completion": {
                            "field": "suggest",
                            "size": limit,
                            "skip_duplicates": True
                        }
                    }
                }
            }
            
            # 执行建议查询
            response_obj = await es.search(
                index=self.index_name,
                body=suggest_body
            )
            
            # 处理结果
            suggestions = []
            if 'suggest' in response_obj:
                for suggestion_type in response_obj['suggest']:
                    for suggestion in response_obj['suggest'][suggestion_type]:
                        for option in suggestion.get('options', []):
                            suggestions.append(option.get('text'))
            
            return list(set(suggestions))[:limit]
            
        except Exception as e:
            logger.error(f"获取搜索建议失败: {str(e)}", exc_info=True)
            return []
    
    # 其他方法可以根据需要修复...
