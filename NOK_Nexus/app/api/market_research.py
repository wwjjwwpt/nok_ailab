"""
市场调研 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Optional

from ..core.database import get_db
from ..schemas.market_research import (
    MarketResearchCreate,
    MarketResearchUpdate,
    MarketResearchResponse,
    MarketResearchListResponse,
)
from ..models.market_research import MarketResearch
from ..core.deps import get_current_user
from ..models import User

router = APIRouter(tags=["市场调研"])


@router.get("", response_model=MarketResearchListResponse)
async def get_research_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    city: Optional[str] = Query(None, description="城市筛选"),
    manufacturer: Optional[str] = Query(None, description="厂商筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取调研列表（仅当前用户的数据）"""
    # 查询当前用户的调研数据
    query = db.query(MarketResearch).filter(
        MarketResearch.user_id == current_user.id,
        MarketResearch.status == 1
    )

    # 筛选条件
    if city:
        query = query.filter(MarketResearch.city.ilike(f"%{city}%"))
    if manufacturer:
        query = query.filter(MarketResearch.manufacturer.ilike(f"%{manufacturer}%"))

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = query.order_by(MarketResearch.created_at.desc()).offset(offset).limit(page_size).all()

    return {
        "items": [item.to_dict() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": offset + page_size < total
    }


@router.get("/{research_id}", response_model=MarketResearchResponse)
async def get_research(
    research_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取调研详情"""
    research = db.query(MarketResearch).filter(
        MarketResearch.id == research_id,
        MarketResearch.user_id == current_user.id,
        MarketResearch.status == 1
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="调研记录不存在")

    return research.to_dict()


@router.post("", response_model=MarketResearchResponse)
async def create_research(
    data: MarketResearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建调研记录"""
    research = MarketResearch(
        user_id=current_user.id,
        city=data.city,
        manufacturer=data.manufacturer,
        product_name=data.product_name,
        price=data.price,
        research_date=data.research_date,
        remark=data.remark,
        created_by=current_user.id,
    )

    db.add(research)
    db.commit()
    db.refresh(research)

    return research.to_dict()


@router.put("/{research_id}", response_model=MarketResearchResponse)
async def update_research(
    research_id: int,
    data: MarketResearchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新调研记录"""
    research = db.query(MarketResearch).filter(
        MarketResearch.id == research_id,
        MarketResearch.user_id == current_user.id,
        MarketResearch.status == 1
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="调研记录不存在")

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(research, field, value)

    research.updated_by = current_user.id

    db.commit()
    db.refresh(research)

    return research.to_dict()


@router.delete("/{research_id}")
async def delete_research(
    research_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除调研记录（软删除）"""
    research = db.query(MarketResearch).filter(
        MarketResearch.id == research_id,
        MarketResearch.user_id == current_user.id,
        MarketResearch.status == 1
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="调研记录不存在")

    research.status = 0
    db.commit()

    return {"message": "删除成功"}
