# 网页快照模块
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Dict, Any
from starlette.responses import HTMLResponse
from datetime import datetime
import logging
import base64

from app.core.config import settings
from app.services.elasticsearch_service import ElasticsearchService
from app.services.user_service import get_optional_user
from app.models.schemas import UserProfile

# 创建路由器
router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取Elasticsearch服务实例
es_service = ElasticsearchService()


@router.get("/{url_id}", response_class=HTMLResponse)
async def get_snapshot(
    url_id: str = Path(..., description="URL的唯一标识符"),
    timestamp: Optional[datetime] = Query(None, description="快照时间点"),
    current_user: Optional[UserProfile] = Depends(get_optional_user),
) -> str:
    """
    获取网页快照，返回HTML内容。

    - **url_id**: URL的唯一标识符
    - **timestamp**: 可选的时间戳，指定获取特定时间点的快照
    """
    try:
        # 获取快照HTML内容
        snapshot = await es_service.get_snapshot(url_id, timestamp)

        if not snapshot:
            raise HTTPException(status_code=404, detail=f"快照不存在: {url_id}")

        # 构建包含CSS样式的HTML页面
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>网页快照 - {snapshot.get('title', '无标题')}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px;
                    line-height: 1.6;
                }}
                .snapshot-header {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-bottom: 1px solid #ddd;
                    margin-bottom: 20px;
                }}
                .snapshot-content {{
                    background-color: white;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .snapshot-footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
                a {{ color: #1a0dab; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="snapshot-header">
                <h2>{snapshot.get('title', '无标题')}</h2>
                <p>原始URL: <a href="{snapshot.get('url', '#')}" target="_blank">{snapshot.get('url', '未知URL')}</a></p>
                <p>快照时间: {snapshot.get('crawl_time', '未知时间')}</p>
            </div>
            <div class="snapshot-content">
                {snapshot.get('html', '快照内容不可用')}
            </div>
            <div class="snapshot-footer">
                <p>由南开大学搜索引擎提供的网页快照 | 当前显示的网页可能已过期</p>
            </div>
        </body>
        </html>
        """

        return html_content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取网页快照出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"快照服务错误: {str(e)}")


@router.get("/info/{url_id}", response_model=Dict[str, Any])
async def get_snapshot_info(
    url_id: str = Path(..., description="URL的唯一标识符"),
    current_user: Optional[UserProfile] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    获取网页快照的元信息，不包含HTML内容。

    - **url_id**: URL的唯一标识符
    """
    try:
        # 获取快照信息
        snapshot_info = await es_service.get_snapshot_info(url_id)

        if not snapshot_info:
            raise HTTPException(status_code=404, detail=f"快照不存在: {url_id}")

        return {"success": True, "snapshot_info": snapshot_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取快照信息出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"快照服务错误: {str(e)}")
