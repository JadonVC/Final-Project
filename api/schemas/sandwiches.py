from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SandwichBase(BaseModel):
    sandwich_name: str
    price: float
    description: Optional[str] = None
    calories: Optional[int] = None
    category: Optional[str] = None  # "vegetarian,spicy,kids,low-fat"
    is_available: bool = True


class SandwichCreate(SandwichBase):
    pass


class SandwichUpdate(BaseModel):
    sandwich_name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None


class Sandwich(SandwichBase):
    id: int
    created_date: datetime

    class ConfigDict:
        from_attributes = True