"""
市场调研模型
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Numeric,
    DateTime,
    Date,
    ForeignKey,
    Text,
    SmallInteger,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class MarketResearch(Base):
    """市场调研表"""

    __tablename__ = "market_researches"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True, comment="创建人 ID")

    # 调研信息
    city = Column(String(100), nullable=False, comment="调研城市")
    manufacturer = Column(String(200), nullable=False, comment="厂商名称")
    product_name = Column(String(200), nullable=False, comment="商品名称")
    price = Column(Numeric(12, 2), nullable=False, comment="调研价格")
    research_date = Column(Date, nullable=False, default=func.current_date(), comment="调研日期")
    remark = Column(Text, comment="备注信息")

    # 状态
    status = Column(SmallInteger, default=1, comment="0-删除 1-正常")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(BigInteger, ForeignKey("users.id"), comment="创建人")
    updated_by = Column(BigInteger, ForeignKey("users.id"), comment="更新人")

    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    user = relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "city": self.city,
            "manufacturer": self.manufacturer,
            "product_name": self.product_name,
            "price": float(self.price) if self.price else 0,
            "research_date": self.research_date.isoformat() if self.research_date else None,
            "remark": self.remark,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "creator": self.creator.nickname if self.creator else None,
            "updater": self.updater.nickname if self.updater else None,
        }
