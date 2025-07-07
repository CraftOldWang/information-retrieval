from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.history import SnapshotResponse
from app.services.history_service import SnapshotService

router = APIRouter()

@router.get("/{url_id}", response_model=SnapshotResponse)
async def get_snapshot(
    url_id: str = Path(..., description="URL ID"),
    timestamp: Optional[datetime] = Query(None, description="快照时间戳"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取网页快照"""
    snapshot_service = SnapshotService()
    snapshot = await snapshot_service.get_snapshot(db, url_id, timestamp)
    
    return SnapshotResponse(snapshot=snapshot)