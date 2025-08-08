from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .order_details import OrderDetail


class OrderBase(BaseModel):
    customer_name: str
    phone: str
    address: Optional[str] = None  # Required for delivery, optional for takeout
    order_type: str  # "takeout" or "delivery"
    description: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None  # "received", "preparing", "ready", "completed"
    payment_status: Optional[str] = None  # "pending", "paid", "failed"
    description: Optional[str] = None


class Order(OrderBase):
    id: int
    order_date: datetime
    status: str = "received"
    total_amount: float
    tracking_number: str
    payment_status: str = "pending"
    order_details: Optional[list[OrderDetail]] = None

    class ConfigDict:
        from_attributes = True