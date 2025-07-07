import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_scan

from app.core.config import settings
from app.core.exceptions import ElasticsearchException, NotFoundException
from app.schemas.search import (
    SearchQuery, DocumentSearchQuery, SearchResultItem, DocumentResultItem,
    SearchResponse, DocumentSearchResponse
)

logger = logging.getLogger(__name__)

class ElasticsearchService:
    """Elasticsearch服务类，使用单例模式"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ElasticsearchService, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """初始化Elasticsearch客户端"""
        if self._client is None:
            try:
                auth = None
                if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
                    auth = (settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
                
                self._client = AsyncElasticsearch(
                    settings.ELASTICSEARCH_HOSTS,
                    http_auth=auth,
                )
                logger.info("Elasticsearch client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Elasticsearch client: {e}")
                raise ElasticsearchException(f"Failed to initialize Elasticsearch: {str(e)}")
    
    async def close(self):
        """关闭Elasticsearch客户端"""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Elasticsearch client closed")
    
    async def get_client(self) -> AsyncElasticsearch:
        """获取Elasticsearch客户端"""
        if self._client is None:
            await self.initialize()
        return self._client
    
    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行搜索"""
        try:
            client = await self.get_client()
            start_time = time.time()
            
            # 构建搜索查询
            search_query = await self._build_search_query(query)
            # 执行搜索，添加严格的分页和超时控制
            response = await client.search(
                index=settings.ELASTICSEARCH_INDEX,  # 使用nku_webpages索引
                body=search_query,
                from_=(query.page - 1) * query.page_size,
                size=min(query.page_size, 50),  # 限制最大页面大小
                timeout="2s",  # 添加超时限制
                request_timeout=5  # 请求超时
            )
            
            # 处理搜索结果
            results = await self._process_search_results(response)
            
            # 计算搜索时间
            search_time = time.time() - start_time
            
            # 获取相关查询
            related_queries = await self._get_related_queries(query.query)
            
            # 构建响应
            return SearchResponse(
                results=results,
                page=query.page,
                page_size=query.page_size,
                total_pages=(response["hits"]["total"]["value"] + query.page_size - 1) // query.page_size,
                total_results=response["hits"]["total"]["value"],
                query=query.query,
                search_time=round(search_time, 3),
                related_queries=related_queries
            )
        except NotFoundError:
            raise NotFoundException("Index not found")
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise ElasticsearchException(f"Search error: {str(e)}")
    
    async def search_documents(self, query: DocumentSearchQuery) -> DocumentSearchResponse:
        """执行文档搜索"""
        try:
            client = await self.get_client()
            start_time = time.time()
            
            # 构建文档搜索查询
            search_query = await self._build_document_search_query(query)
            
            # 执行搜索，添加严格的分页和超时控制
            response = await client.search(
                index=settings.ELASTICSEARCH_INDEX,
                body=search_query,
                from_=(query.page - 1) * query.page_size,
                size=min(query.page_size, 50),  # 限制最大页面大小
                timeout="2s",  # 添加超时限制
                request_timeout=5  # 请求超时
            )
            
            # 处理搜索结果
            results = await self._process_document_results(response)
            
            # 计算搜索时间
            search_time = time.time() - start_time
            
            # 构建响应
            return DocumentSearchResponse(
                results=results,
                page=query.page,
                page_size=query.page_size,
                total_pages=(response["hits"]["total"]["value"] + query.page_size - 1) // query.page_size,
                total_results=response["hits"]["total"]["value"],
                query=query.query,
                search_time=round(search_time, 3)
            )
        except NotFoundError:
            raise NotFoundException("Index not found")
        except Exception as e:
            logger.error(f"Document search error: {e}")
            raise ElasticsearchException(f"Document search error: {str(e)}")
    
    async def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """获取搜索建议"""
        try:
            client = await self.get_client()
            
            # 使用简单的match查询替代completion suggest，避免字段类型问题
            suggestion_query = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match_phrase_prefix": {
                                    "title": {
                                        "query": query,
                                        "max_expansions": 10
                                    }
                                }
                            },
                            {
                                "match_phrase_prefix": {
                                    "content": {
                                        "query": query,
                                        "max_expansions": 5
                                    }
                                }
                            }
                        ]
                    }
                },
                "_source": ["title"],  # 只返回需要的字段
                "size": limit,
                "timeout": "1s"  # 添加超时限制
            }
            
            # 执行建议查询
            response = await client.search(
                index=settings.ELASTICSEARCH_INDEX,
                body=suggestion_query
            )
            
            # 处理建议结果
            suggestions = set()
            for hit in response["hits"]["hits"]:
                title = hit["_source"].get("title", "")
                if title and query.lower() in title.lower():
                    suggestions.add(title)
            
            return list(suggestions)[:limit]
        except Exception as e:
            logger.error(f"Get suggestions error: {e}")
            return []
    
    async def get_recommendations(self, query: str, limit: int = 5) -> List[str]:
        """获取搜索推荐"""
        try:
            client = await self.get_client()
            
            # 使用简化的查询避免大规模聚合，减少内存使用
            recommendation_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2"],  # 只搜索标题字段，减少内存使用
                        "type": "phrase_prefix"
                    }
                },
                "_source": ["title"],  # 只返回标题字段
                "size": min(limit * 2, 20),  # 限制返回数量
                "timeout": "500ms"  # 添加超时限制
            }
            
            # 执行推荐查询
            response = await client.search(
                index=settings.ELASTICSEARCH_INDEX,
                body=recommendation_query
            )
            
            # 处理推荐结果 - 提取相关词汇
            recommendations = set()
            for hit in response["hits"]["hits"]:
                title = hit["_source"].get("title", "")
                if title:
                    # 简单的词汇提取，避免复杂的文本分析
                    words = title.split()
                    for word in words:
                        if len(word) > 2 and word.lower() != query.lower():
                            recommendations.add(word)
                            if len(recommendations) >= limit:
                                break
                if len(recommendations) >= limit:
                    break
            
            return list(recommendations)[:limit]
        except Exception as e:
            logger.error(f"Get recommendations error: {e}")
            return []
    
    async def _build_search_query(self, query: SearchQuery) -> Dict[str, Any]:
        """构建搜索查询"""
        # 基础查询
        search_query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 0},
                    "content": {"fragment_size": 100, "number_of_fragments": 1}  # 减少片段数量和大小
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            },
            "_source": {
                "excludes": ["content"]  # 排除大字段，减少传输数据
            }
        }
        
        # 根据搜索类型构建查询
        if query.search_type == "phrase":
            search_query["query"]["bool"]["must"].append({
                "match_phrase": {"content": query.query}
            })
        elif query.search_type == "wildcard":
            # 在多个字段上进行通配符查询
            wildcard_queries = [
                {"wildcard": {"title": f"*{query.query}*"}},
                {"wildcard": {"content": f"*{query.query}*"}},
                {"wildcard": {"anchor_texts.text": f"*{query.query}*"}}
            ]
            search_query["query"]["bool"]["must"].append({
                "bool": {
                    "should": wildcard_queries,
                    "minimum_should_match": 1
                }
            })
        else:  # 默认为normal
            search_query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query.query,
                    "fields": ["title^3", "content", "anchor_texts.text"]
                }
            })
        
        # 添加过滤条件
        if query.domain_filter:
            search_query["query"]["bool"]["filter"].append({
                "terms": {"domain": query.domain_filter}
            })
        
        if query.date_from or query.date_to:
            date_filter = {"range": {"metadata.crawl_time": {}}}
            if query.date_from:
                date_filter["range"]["metadata.crawl_time"]["gte"] = query.date_from.isoformat()
            if query.date_to:
                date_filter["range"]["metadata.crawl_time"]["lte"] = query.date_to.isoformat()
            search_query["query"]["bool"]["filter"].append(date_filter)
        
        if query.file_type:
            search_query["query"]["bool"]["filter"].append({
                "terms": {"metadata.content_type": query.file_type}
            })
        
        return search_query
    
    async def _build_document_search_query(self, query: DocumentSearchQuery) -> Dict[str, Any]:
        """构建文档搜索查询"""
        # 基础查询
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "nested": {
                                "path": "attachments",
                                "query": {
                                    "bool": {
                                        "must": [],
                                        "filter": []
                                    }
                                },
                                "inner_hits": {
                                    "highlight": {
                                        "fields": {
                                            "attachments.filename": {"number_of_fragments": 0},
                                            "attachments.metadata.title": {"number_of_fragments": 0}
                                        },
                                        "pre_tags": ["<mark>"],
                                        "post_tags": ["</mark>"]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        # 添加文档类型过滤
        if query.doc_types:
            search_query["query"]["bool"]["must"][0]["nested"]["query"]["bool"]["filter"].append({
                "terms": {"attachments.type": query.doc_types}
            })
        
        # 添加日期过滤
        if query.date_from or query.date_to:
            date_filter = {"range": {"attachments.metadata.upload_date": {}}}
            if query.date_from:
                date_filter["range"]["attachments.metadata.upload_date"]["gte"] = query.date_from.isoformat()
            if query.date_to:
                date_filter["range"]["attachments.metadata.upload_date"]["lte"] = query.date_to.isoformat()
            search_query["query"]["bool"]["must"][0]["nested"]["query"]["bool"]["filter"].append(date_filter)
        
        # 根据搜索类型添加查询条件
        if query.search_type == "phrase":
            search_query["query"]["bool"]["must"][0]["nested"]["query"]["bool"]["must"].append({
                "match_phrase": {
                    "attachments.filename": query.query
                }
            })
            search_query["query"]["bool"]["must"][0]["nested"]["query"]["bool"]["must"].append({
                "match_phrase": {
                    "attachments.metadata.title": query.query
                }
            })
        elif query.search_type == "wildcard":
            # 文档通配符查询
            wildcard_queries = [
                {"wildcard": {"attachments.filename": f"*{query.query}*"}},
                {"wildcard": {"attachments.metadata.title": f"*{query.query}*"}}
            ]
            search_query["query"]["bool"]["must"][0]["nested"]["query"]["bool"]["must"].append({
                "bool": {
                    "should": wildcard_queries,
                    "minimum_should_match": 1
                }
            })
        else:  # 默认为normal
            search_query["query"]["bool"]["must"][0]["nested"]["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query.query,
                    "fields": [
                        "attachments.filename^2",
                        "attachments.metadata.title^3"
                    ]
                }
            })
        
        return search_query
    
    async def _process_search_results(self, response: Dict[str, Any]) -> List[SearchResultItem]:
        """处理搜索结果"""
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # 提取高亮内容
            highlights = {}
            if "highlight" in hit:
                for field, value in hit["highlight"].items():
                    highlights[field] = value
            
            # 从高亮中获取内容片段，因为我们排除了content字段
            content_snippet = None
            if highlights.get("content"):
                content_snippet = " ".join(highlights["content"])
            
            # 创建结果项
            result = SearchResultItem(
                id=hit["_id"],
                url=source.get("url", ""),
                title=source.get("title", ""),
                snippet=content_snippet,
                content=None,  # 不返回完整内容，减少内存使用
                domain=source.get("domain"),
                date=source.get("metadata", {}).get("crawl_time"),
                highlights={
                    "title": highlights.get("title"),
                    "content": highlights.get("content")
                },
                score=hit["_score"],
                metadata=source.get("metadata")
            )
            
            results.append(result)
        
        return results
    
    async def _process_document_results(self, response: Dict[str, Any]) -> List[DocumentResultItem]:
        """处理文档搜索结果"""
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # 获取内部命中的附件
            if "inner_hits" in hit and "attachments" in hit["inner_hits"]:
                for inner_hit in hit["inner_hits"]["attachments"]["hits"]["hits"]:
                    inner_source = inner_hit["_source"]
                    
                    # 提取高亮内容
                    highlights = {}
                    if "highlight" in inner_hit:
                        for field, value in inner_hit["highlight"].items():
                            field_name = field.split(".")[-1]  # 获取字段名称
                            highlights[field_name] = value
                    
                    # 创建结果项
                    result = DocumentResultItem(
                        id=hit["_id"] + "_" + inner_hit["_id"],
                        url=source.get("url", "") + "#" + inner_source.get("url", ""),
                        title=inner_source.get("metadata", {}).get("title", inner_source.get("filename", "")),
                        filename=inner_source.get("filename", ""),
                        type=inner_source.get("type", ""),
                        snippet=None,  # 文档没有片段
                        author=inner_source.get("metadata", {}).get("author"),
                        upload_date=inner_source.get("metadata", {}).get("upload_date"),
                        file_size=inner_source.get("metadata", {}).get("file_size"),
                        highlights={
                            "title": highlights.get("title") or highlights.get("filename"),
                            "content": None
                        },
                        score=inner_hit["_score"]
                    )
                    
                    results.append(result)
        
        return results
    
    async def _get_related_queries(self, query: str) -> List[str]:
        """获取相关查询"""
        try:
            # 这里可以实现更复杂的相关查询逻辑
            # 简单实现：使用查询词的一部分作为相关查询
            words = query.split()
            related = []
            
            if len(words) > 1:
                # 使用查询中的部分词组合作为相关查询
                for i in range(len(words)):
                    related_query = " ".join(words[:i] + words[i+1:])
                    if related_query and related_query != query:
                        related.append(related_query)
            
            # 如果没有足够的相关查询，可以调用推荐API
            if len(related) < 5:
                recommendations = await self.get_recommendations(query)
                for rec in recommendations:
                    if rec not in related and rec != query:
                        related.append(rec)
            
            return related[:5]  # 最多返回5个相关查询
        except Exception as e:
            logger.error(f"Get related queries error: {e}")
            return []