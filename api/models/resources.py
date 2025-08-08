from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item = Column(String(100), unique=True, nullable=False)
    amount = Column(Integer, index=True, nullable=False, server_default='0')
    unit = Column(String(20), nullable=False, server_default="piece")  # "piece", "oz", "cup", "slice", "lb", etc.
    minimum_stock = Column(Integer, nullable=False, server_default='10')  # Alert threshold
    cost_per_unit = Column(DECIMAL(8, 2), nullable=True)  # Optional: for cost tracking

    recipes = relationship("Recipe", back_populates="resource")