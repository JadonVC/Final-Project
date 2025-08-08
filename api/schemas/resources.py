from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ResourceBase(BaseModel):
    item: str
    amount: int
    unit: str = "piece"  # "piece", "oz", "cup", "slice", "lb", etc.
    minimum_stock: int = 10
    cost_per_unit: Optional[float] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    item: Optional[str] = None
    amount: Optional[int] = None
    unit: Optional[str] = None
    minimum_stock: Optional[int] = None
    cost_per_unit: Optional[float] = None


class Resource(ResourceBase):
    id: int

    class ConfigDict:
        from_attributes = True