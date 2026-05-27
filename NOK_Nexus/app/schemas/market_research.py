"""
市场调研 Schema
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class MarketResearchBase(BaseModel):
    """市场调研基础模型"""

    city: str = Field(..., min_length=1, max_length=100, description="调研城市")
    manufacturer: str = Field(..., min_length=1, max_length=200, description="厂商名称")
    product_name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    price: float = Field(..., gt=0, le=9999999999.99, description="调研价格")
    research_date: Optional[date] = Field(default=None, description="调研日期")
    remark: Optional[str] = Field(default=None, max_length=1000, description="备注信息")


class MarketResearchCreate(MarketResearchBase):
    """创建市场调研"""

    pass


class MarketResearchUpdate(BaseModel):
    """更新市场调研"""

    city: Optional[str] = Field(default=None, min_length=1, max_length=100, description="调研城市")
    manufacturer: Optional[str] = Field(default=None, min_length=1, max_length=200, description="厂商名称")
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="商品名称")
    price: Optional[float] = Field(default=None, gt=0, le=9999999999.99, description="调研价格")
    research_date: Optional[date] = Field(default=None, description="调研日期")
    remark: Optional[str] = Field(default=None, max_length=1000, description="备注信息")
    status: Optional[int] = Field(default=None, description="状态")


class MarketResearchResponse(MarketResearchBase):
    """市场调研响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: int
    created_at: datetime
    updated_at: datetime
    creator: Optional[str] = None
    updater: Optional[str] = None


class MarketResearchListResponse(BaseModel):
    """市场调研列表响应"""

    items: List[MarketResearchResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
