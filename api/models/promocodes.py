from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # "SAVE5", "WELCOME10"
    discount_amount = Column(DECIMAL(6, 2), nullable=False)  # Fixed dollar amount off (e.g., 5.00 for $5 off)
    expiration_date = Column(DATETIME, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default='1')

    # Usage management
    usage_limit = Column(Integer, nullable=False)  # How many times code can be used
    times_used = Column(Integer, nullable=False, server_default='0')  # Track usage count
    minimum_order_amount = Column(DECIMAL(8, 2), nullable=False)  # Minimum order required

    # Management info
    created_date = Column(DATETIME, nullable=False, server_default=str(datetime.now()))
    description = Column(String(300), nullable=True)  # "First time customer discount", "Holiday special"

    # Relationships - track which orders used this code
    orders = relationship("Order", back_populates="promo_code")