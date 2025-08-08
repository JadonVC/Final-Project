from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, DATETIME
from sqlalchemy.orm import relationship
from datetime import datetime
from ..dependencies.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sandwich_id = Column(Integer, ForeignKey("sandwiches.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    amount = Column(Integer, index=True, nullable=False, server_default='1')
    unit = Column(String(20), nullable=False, server_default="piece")  # "piece", "oz", "cup", "slice", etc.

    sandwich = relationship("Sandwich", back_populates="recipes")
    resource = relationship("Resource", back_populates="recipes")