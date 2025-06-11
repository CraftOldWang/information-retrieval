# 文档搜索模块
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.config import settings
from app.services.elasticsearch_service import ElasticsearchService
from app.models.schemas import SearchQuery, SearchResponse
from app.services.user_service import get_current_user, get_optional_user
from app.models.schemas import UserProfile

# 创建路由器
router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取Elasticsearch服务实例
es_service = ElasticsearchService()


@router.get("/", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页结果数"),
    doc_type: Optional[List[str]] = Query(
        None, description="文档类型过滤，如pdf, doc, ppt等"
    ),
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    current_user: Optional[UserProfile] = Depends(get_optional_user),
) -> SearchResponse:
    """
    文档搜索API，专门用于搜索文档类型内容。

    - **q**: 搜索关键词
    - **page**: 页码 (从1开始)
    - **page_size**: 每页结果数
    - **doc_type**: 文档类型过滤 (pdf, doc, docx, ppt, pptx, xls, xlsx等)
    - **date_from**: 开始日期过滤
    - **date_to**: 结束日期过滤
    """
    try:
        # 构建搜索查询
        query = SearchQuery(
            query=q,
            page=page,
            page_size=page_size,
            search_type="document",
            date_from=date_from,
            date_to=date_to,
        )

        # 执行文档搜索
        results = await es_service.search_documents(query, doc_type, current_user)

        # 如果用户已登录，记录搜索历史
        if current_user:
            await es_service.record_search_history(
                current_user.id, query, results.total
            )

        return results
    except Exception as e:
        logger.error(f"文档搜索出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文档搜索服务错误: {str(e)}")


@router.get("/{doc_id}", response_model=Dict[str, Any])
async def get_document_metadata(
    doc_id: str,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    获取单个文档的元数据。

    - **doc_id**: 文档ID
    """
    try:
        document = await es_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"文档不存在: {doc_id}")

        return {"success": True, "document": document}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档元数据出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文档服务错误: {str(e)}")
