from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base


class OrderDetail(Base):
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sandwich_id = Column(Integer, ForeignKey("sandwiches.id"), nullable=False)
    amount = Column(Integer, index=True, nullable=False, server_default='1')
    unit_price = Column(DECIMAL(6, 2), nullable=False)  # Price at time of order
    subtotal = Column(DECIMAL(8, 2), nullable=False)  # amount * unit_price
    special_instructions = Column(String(300), nullable=True)  # "No tomatoes", "Extra sauce", etc.

    sandwich = relationship("Sandwich", back_populates="order_details")
    order = relationship("Order", back_populates="order_details")