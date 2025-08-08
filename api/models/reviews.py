from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base
from .sandwiches import Sandwich


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sandwich_id = Column(Integer, ForeignKey("sandwiches.id"), nullable=False)
    customer_name = Column(String(100), nullable=False)  # From the order
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)  # Customer review text
    review_date = Column(DATETIME, nullable=False, server_default=str(datetime.now()))

    # Staff response feature
    staff_response = Column(Text, nullable=True)  # Restaurant can respond
    response_date = Column(DATETIME, nullable=True)  # When staff responded

    # Relationships
    order = relationship("Order", back_populates="reviews")
    sandwich = relationship("Sandwich", back_populates="reviews")