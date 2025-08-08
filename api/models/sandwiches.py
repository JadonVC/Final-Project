from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base
from .recipes import Recipe


class Sandwich(Base):
    __tablename__ = "sandwiches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sandwich_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)  # What's in the sandwich
    price = Column(DECIMAL(6, 2), nullable=False, server_default='0.00')
    calories = Column(Integer, nullable=True)  # Optional nutrition info
    category = Column(String(100), nullable=True)  # "vegetarian,spicy,kids,low-fat" (comma-separated)
    is_available = Column(Boolean, nullable=False, server_default='1')  # Available/unavailable
    created_date = Column(DATETIME, nullable=False, server_default=str(datetime.now()))

    recipes = relationship("Recipe", back_populates="sandwich")
    order_details = relationship("OrderDetail", back_populates="sandwich")

    # Testing
    reviews = relationship("Review", back_populates="sandwich")
