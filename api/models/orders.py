from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base
from .reviews import Review


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    address = Column(String(500))  # For delivery orders
    order_date = Column(DATETIME, nullable=False, server_default=str(datetime.now()))
    order_type = Column(String(20), nullable=False)  # "takeout" or "delivery"
    status = Column(String(50), nullable=False, server_default="received")  # "received", "preparing", "ready", "completed"
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    tracking_number = Column(String(50), unique=True, nullable=False)
    payment_status = Column(String(20), nullable=False, server_default="pending")  # "pending", "paid", "failed"
    description = Column(String(300))

    # Testing
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"))
    promo_code = relationship("PromoCode", back_populates="orders")
    reviews = relationship("Review", back_populates="order")

    order_details = relationship("OrderDetail", back_populates="order")