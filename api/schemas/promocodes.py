from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PromoCodeBase(BaseModel):
    code: str
    discount_amount: float
    expiration_date: datetime
    usage_limit: int
    minimum_order_amount: float
    description: Optional[str] = None
    is_active: bool = True


class PromoCodeCreate(PromoCodeBase):
    pass


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    discount_amount: Optional[float] = None
    expiration_date: Optional[datetime] = None
    usage_limit: Optional[int] = None
    minimum_order_amount: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PromoCode(PromoCodeBase):
    id: int
    times_used: int
    created_date: datetime

    class ConfigDict:
        from_attributes = True


class PromoCodeValidation(BaseModel):
    """Schema for validating promo codes during order placement"""
    code: str
    order_total: float


class PromoCodeValidationResponse(BaseModel):
    """Response after validating a promo code"""
    is_valid: bool
    discount_amount: float
    message: str  # "Valid discount applied" or "Code expired", etc.