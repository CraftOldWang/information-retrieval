# 推荐服务模块
import logging
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import re
from collections import Counter

from app.core.config import settings
from app.models.schemas import UserProfile, RecommendationResponse, RecommendationItem
from app.services.history_service import HistoryService
from app.services.elasticsearch_service import ElasticsearchService

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐服务类"""
    
    def __init__(self):
        self.db_path = settings.SQLITE_DATABASE_URL
        self.history_service = HistoryService()
        self.es_service = ElasticsearchService()
        self._init_database()
    
    def _init_database(self):
        """初始化推荐数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建查询关联表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_associations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query1 TEXT NOT NULL,
                        query2 TEXT NOT NULL,
                        association_score REAL DEFAULT 1.0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建热门查询缓存表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS popular_queries_cache (
                        query TEXT PRIMARY KEY,
                        count INTEGER NOT NULL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"初始化推荐数据库失败: {str(e)}", exc_info=True)
            raise
    
    async def get_query_recommendations(self, input_query: str, limit: int = 10, 
                                      user: Optional[UserProfile] = None) -> List[str]:
        """获取查询词推荐（自动补全）"""
        try:
            recommendations = []
            
            # 1. 基于前缀匹配的历史查询
            prefix_matches = await self._get_prefix_matches(input_query, limit // 2, user)
            recommendations.extend(prefix_matches)
            
            # 2. 基于相似度的查询推荐
            similar_queries = await self._get_similar_queries(input_query, limit - len(recommendations), user)
            recommendations.extend(similar_queries)
            
            # 3. 如果还没有足够的推荐，添加热门查询
            if len(recommendations) < limit:
                popular = await self.get_popular_queries(limit - len(recommendations))
                for query in popular:
                    if query not in recommendations and input_query.lower() in query.lower():
                        recommendations.append(query)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"获取查询推荐失败: {str(e)}", exc_info=True)
            return []
    
    async def get_related_queries(self, query: str, limit: int = 5, 
                                user: Optional[UserProfile] = None) -> List[str]:
        """获取相关查询"""
        try:
            related_queries = []
            
            # 1. 基于查询关联表
            associations = await self._get_query_associations(query, limit)
            related_queries.extend(associations)
            
            # 2. 基于用户历史的相关查询
            if user:
                user_related = await self._get_user_related_queries(query, user.id, limit - len(related_queries))
                related_queries.extend(user_related)
            
            # 3. 基于文本相似度的查询
            if len(related_queries) < limit:
                similar = await self._get_text_similar_queries(query, limit - len(related_queries))
                related_queries.extend(similar)
            
            return list(set(related_queries))[:limit]
            
        except Exception as e:
            logger.error(f"获取相关查询失败: {str(e)}", exc_info=True)
            return []
    
    async def get_popular_queries(self, limit: int = 10) -> List[str]:
        """获取热门查询"""
        try:
            # 先尝试从缓存获取
            cached_queries = await self._get_cached_popular_queries(limit)
            if cached_queries:
                return cached_queries
            
            # 从历史记录计算热门查询
            popular = await self.history_service.get_popular_queries(limit * 2)  # 获取更多数据用于过滤
            
            # 过滤太短或无意义的查询
            filtered_queries = []
            for item in popular:
                query = item['query'].strip()
                if len(query) >= 2 and self._is_meaningful_query(query):
                    filtered_queries.append(query)
            
            result = filtered_queries[:limit]
            
            # 更新缓存
            await self._update_popular_queries_cache(result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取热门查询失败: {str(e)}", exc_info=True)
            return []
    
    async def get_personalized_recommendations(self, user: UserProfile, limit: int = 10) -> RecommendationResponse:
        """获取个性化推荐"""
        try:
            recommendations = []
              # 1. 基于用户查询历史的推荐
            query_patterns = await self.history_service.get_user_query_patterns(user.id, 10)
            for query in query_patterns[:5]:
                related = await self.get_related_queries(query, 2, user)
                for rel_query in related:
                    if rel_query not in [r.content for r in recommendations]:
                        recommendations.append(RecommendationItem(
                            type="query",
                            content=rel_query,
                            score=0.8,
                            reason=f"基于您的搜索「{query}」"
                        ))
            
            # 2. 基于用户偏好的内容推荐
            user_prefs = await self._get_user_preferences_insights(user.id)
            if user_prefs:
                content_recs = await self._get_preference_based_recommendations(user_prefs, limit // 2)
                recommendations.extend(content_recs)
            
            # 3. 热门内容推荐
            if len(recommendations) < limit:
                popular_recs = await self._get_popular_content_recommendations(limit - len(recommendations))
                recommendations.extend(popular_recs)
            
            return RecommendationResponse(
                recommendations=recommendations[:limit]
            )
            
        except Exception as e:
            logger.error(f"获取个性化推荐失败: {str(e)}", exc_info=True)
            return RecommendationResponse(recommendations=[])
    
    async def _get_prefix_matches(self, prefix: str, limit: int, user: Optional[UserProfile]) -> List[str]:
        """获取前缀匹配的查询"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询，优先匹配用户自己的历史
                if user:
                    cursor.execute("""
                        SELECT query, COUNT(*) as count
                        FROM search_history 
                        WHERE query LIKE ? AND user_id = ?
                        GROUP BY query
                        ORDER BY count DESC, created_at DESC
                        LIMIT ?
                    """, (f"{prefix}%", user.id, limit))
                    user_matches = [row[0] for row in cursor.fetchall()]
                    
                    if len(user_matches) >= limit:
                        return user_matches
                    
                    # 如果用户历史不够，补充全局匹配
                    remaining = limit - len(user_matches)
                    cursor.execute("""
                        SELECT query, COUNT(*) as count
                        FROM search_history 
                        WHERE query LIKE ? AND query NOT IN ({})
                        GROUP BY query
                        ORDER BY count DESC
                        LIMIT ?
                    """.format(','.join(['?' for _ in user_matches])), 
                        [f"{prefix}%"] + user_matches + [remaining])
                    
                    global_matches = [row[0] for row in cursor.fetchall()]
                    return user_matches + global_matches
                else:
                    cursor.execute("""
                        SELECT query, COUNT(*) as count
                        FROM search_history 
                        WHERE query LIKE ?
                        GROUP BY query
                        ORDER BY count DESC
                        LIMIT ?
                    """, (f"{prefix}%", limit))
                    
                    return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取前缀匹配失败: {str(e)}", exc_info=True)
            return []
    
    async def _get_similar_queries(self, query: str, limit: int, user: Optional[UserProfile]) -> List[str]:
        """获取相似查询"""
        try:
            # 简单的字符串相似度匹配
            query_words = set(query.lower().split())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT query FROM search_history 
                    WHERE query != ? 
                    ORDER BY created_at DESC
                    LIMIT 100
                """, (query,))
                
                candidates = [row[0] for row in cursor.fetchall()]
                
                # 计算相似度
                similar_queries = []
                for candidate in candidates:
                    candidate_words = set(candidate.lower().split())
                    intersection = len(query_words & candidate_words)
                    union = len(query_words | candidate_words)
                    
                    if union > 0:
                        similarity = intersection / union
                        if similarity > 0.3:  # 相似度阈值
                            similar_queries.append((candidate, similarity))
                
                # 按相似度排序
                similar_queries.sort(key=lambda x: x[1], reverse=True)
                return [q[0] for q in similar_queries[:limit]]
                
        except Exception as e:
            logger.error(f"获取相似查询失败: {str(e)}", exc_info=True)
            return []
    
    async def _get_query_associations(self, query: str, limit: int) -> List[str]:
        """从关联表获取相关查询"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query2, association_score 
                    FROM query_associations 
                    WHERE query1 = ?
                    ORDER BY association_score DESC
                    LIMIT ?
                """, (query, limit))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取查询关联失败: {str(e)}", exc_info=True)
            return []
    
    async def _get_user_related_queries(self, query: str, user_id: int, limit: int) -> List[str]:
        """获取用户相关的查询"""
        try:
            # 基于用户搜索会话的相关查询
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT h2.query
                    FROM search_history h1
                    JOIN search_history h2 ON h1.user_id = h2.user_id
                    WHERE h1.query = ? AND h1.user_id = ? AND h2.query != ?
                    AND ABS(julianday(h2.created_at) - julianday(h1.created_at)) < 1
                    GROUP BY h2.query
                    ORDER BY COUNT(*) DESC
                    LIMIT ?
                """, (query, user_id, query, limit))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取用户相关查询失败: {str(e)}", exc_info=True)
            return []
    
    async def _get_text_similar_queries(self, query: str, limit: int) -> List[str]:
        """基于文本相似度获取查询"""
        # 使用Elasticsearch的more_like_this查询
        try:
            es = await self.es_service.get_client()
            search_body = {
                "query": {
                    "more_like_this": {
                        "fields": ["title", "content"],
                        "like": query,
                        "min_term_freq": 1,
                        "max_query_terms": 10
                    }
                },
                "size": limit,
                "_source": ["title"]
            }
            
            response = es.search(index=self.es_service.index_name, body=search_body)
            
            # 从标题中提取可能的查询词
            similar_queries = []
            for hit in response['hits']['hits']:
                title = hit['_source'].get('title', '')
                # 简单的关键词提取
                words = re.findall(r'\b\w{2,}\b', title.lower())
                if words:
                    similar_queries.append(' '.join(words[:3]))  # 取前3个词
            
            return list(set(similar_queries))[:limit]
            
        except Exception as e:
            logger.error(f"获取文本相似查询失败: {str(e)}", exc_info=True)
            return []
    
    async def _get_cached_popular_queries(self, limit: int) -> List[str]:
        """从缓存获取热门查询"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query FROM popular_queries_cache 
                    WHERE last_updated > datetime('now', '-1 hour')
                    ORDER BY count DESC
                    LIMIT ?
                """, (limit,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取缓存热门查询失败: {str(e)}", exc_info=True)
            return []
    
    async def _update_popular_queries_cache(self, queries: List[str]):
        """更新热门查询缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 清空旧缓存
                cursor.execute("DELETE FROM popular_queries_cache")
                
                # 插入新缓存
                for i, query in enumerate(queries):
                    cursor.execute("""
                        INSERT INTO popular_queries_cache (query, count)
                        VALUES (?, ?)
                    """, (query, len(queries) - i))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新热门查询缓存失败: {str(e)}", exc_info=True)
    
    async def _get_user_preferences_insights(self, user_id: int) -> Dict[str, Any]:
        """获取用户偏好洞察"""
        try:
            # 从数据库获取用户偏好
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT domain_preferences, topic_preferences
                    FROM user_preferences
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                
                if row:
                    preferences = {
                        "domain_preferences": json.loads(row["domain_preferences"] or "{}"),
                        "topic_preferences": json.loads(row["topic_preferences"] or "{}")
                    }
                    return preferences
                
                # 如果没有显式偏好，从历史中分析
                return await self._analyze_preferences_from_history(user_id)
                
        except Exception as e:
            logger.error(f"获取用户偏好洞察失败: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_preferences_from_history(self, user_id: int) -> Dict[str, Any]:
        """从用户历史行为中分析偏好"""
        try:
            preferences = {
                "domain_preferences": {},
                "topic_preferences": {}
            }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. 分析用户点击的域名偏好
                cursor.execute("""
                    SELECT url, COUNT(*) as count
                    FROM user_feedback
                    WHERE user_id = ? AND action = 'click'
                    GROUP BY domain
                    ORDER BY count DESC
                    LIMIT 10
                """, (user_id,))
                
                domain_clicks = cursor.fetchall()
                
                for row in domain_clicks:
                    url = row['url']
                    count = row['count']
                    # 从URL中提取域名
                    domain = url.split('/')[2] if url.startswith('http') and '/' in url[8:] else url
                    
                    # 计算偏好权重 (1.0-2.0之间)
                    weight = min(1.0 + (count / 10), 2.0)
                    preferences["domain_preferences"][domain] = weight
                
                # 2. 分析用户搜索的关键词
                cursor.execute("""
                    SELECT query, COUNT(*) as count
                    FROM search_history
                    WHERE user_id = ?
                    GROUP BY query
                    ORDER BY count DESC
                    LIMIT 20
                """, (user_id,))
                
                query_counts = cursor.fetchall()
                
                # 简单词频分析
                word_counts = Counter()
                for row in query_counts:
                    query = row['query']
                    count = row['count']
                    
                    # 分词 (这里使用简单的空格分割，实际应使用jieba等工具)
                    words = query.strip().split()
                    for word in words:
                        if len(word) > 1:  # 忽略单字词
                            word_counts[word] += count
                
                # 提取前10个高频词作为兴趣主题
                for word, count in word_counts.most_common(10):
                    # 计算偏好权重 (1.0-1.8之间)
                    weight = min(1.0 + (count / 5 * 0.1), 1.8)
                    preferences["topic_preferences"][word] = weight
            
            return preferences
        
        except Exception as e:
            logger.error(f"分析用户偏好失败: {str(e)}", exc_info=True)
            return {"domain_preferences": {}, "topic_preferences": {}}
    
    async def _get_preference_based_recommendations(self, user_prefs: Dict[str, Any], limit: int) -> List[RecommendationItem]:
        """基于用户偏好的内容推荐"""
        recommendations = []
        
        try:
            es = await self.es_service.get_client()
            
            # 提取用户的偏好主题和域名
            preferred_topics = list(user_prefs.get("topic_preferences", {}).keys())
            preferred_domains = list(user_prefs.get("domain_preferences", {}).keys())
            
            if not preferred_topics and not preferred_domains:
                return []
                
            # 构建查询
            search_body = {
                "query": {
                    "bool": {
                        "should": []
                    }
                },
                "size": limit * 2,  # 获取更多结果以便过滤
                "_source": ["url", "title", "content", "domain", "metadata"]
            }
            
            # 添加主题偏好条件
            if preferred_topics:
                for topic in preferred_topics:
                    search_body["query"]["bool"]["should"].append({
                        "multi_match": {
                            "query": topic,
                            "fields": ["title^3", "content"],
                            "fuzziness": "AUTO"
                        }
                    })
                    
            # 添加域名偏好条件
            if preferred_domains:
                search_body["query"]["bool"]["should"].append({
                    "terms": {
                        "domain": preferred_domains
                    }
                })
                
            # 执行查询
            response = es.search(
                index=self.es_service.index_name,
                body=search_body
            )
            
            # 处理结果
            response_dict = response if isinstance(response, dict) else response.body
            
            for hit in response_dict['hits']['hits']:
                source = hit['_source']
                      # 生成推荐理由
            reason = "根据您的兴趣推荐"
            for topic in preferred_topics:
                if topic.lower() in source.get('title', '').lower():
                    reason = f"与您感兴趣的\"{topic}\"相关"
                    break
                
            if source.get('domain') in preferred_domains:
                reason += f"，来自您常访问的{source.get('domain')}"
                    
                recommendations.append(RecommendationItem(
                    type="content",
                    content=source.get('url'),
                    score=hit['_score'],
                    reason=reason
                ))
                
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"获取基于偏好的推荐失败: {str(e)}", exc_info=True)
            return []
    
    async def _get_popular_content_recommendations(self, limit: int) -> List[RecommendationItem]:
        """获取热门内容推荐"""
        recommendations = []
        
        try:
            es = await self.es_service.get_client()
            
            # 构建查询，获取近期热门内容
            search_body = {
                "query": {
                    "function_score": {
                        "query": {
                            "match_all": {}
                        },
                        "functions": [
                            {
                                "gauss": {
                                    "metadata.crawl_time": {
                                        "scale": "7d",  # 时间衰减，7天为一个尺度
                                        "decay": 0.5
                                    }
                                }
                            }
                        ],
                        "boost_mode": "multiply"
                    }
                },
                "size": limit,
                "_source": ["url", "title", "domain", "metadata"]
            }
            
            # 执行查询
            response = es.search(
                index=self.es_service.index_name,
                body=search_body
            )
            
            # 处理结果
            response_dict = response if isinstance(response, dict) else response.body
            
            for hit in response_dict['hits']['hits']:
                source = hit['_source']
                recommendations.append(RecommendationItem(
                    type="content",
                    content=source.get('url'),
                    score=hit['_score'],
                    reason="热门内容推荐"
                ))
                
            return recommendations
            
        except Exception as e:
            logger.error(f"获取热门内容推荐失败: {str(e)}", exc_info=True)
            return []
