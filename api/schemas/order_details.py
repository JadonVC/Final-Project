from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .sandwiches import Sandwich


class OrderDetailBase(BaseModel):
    amount: int
    special_instructions: Optional[str] = None  # "No tomatoes", "Extra sauce", etc.


class OrderDetailCreate(OrderDetailBase):
    order_id: int
    sandwich_id: int
    unit_price: float  # Price at time of order


class OrderDetailUpdate(BaseModel):
    order_id: Optional[int] = None
    sandwich_id: Optional[int] = None
    amount: Optional[int] = None
    unit_price: Optional[float] = None
    special_instructions: Optional[str] = None


class OrderDetail(OrderDetailBase):
    id: int
    order_id: int
    sandwich_id: int
    unit_price: float
    subtotal: float  # amount * unit_price (calculated)
    sandwich: Optional[Sandwich] = None

    class ConfigDict:
        from_attributes = True