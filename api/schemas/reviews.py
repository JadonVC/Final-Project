from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .sandwiches import Sandwich


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)  # Must be between 1-5 stars
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    order_id: int
    sandwich_id: int
    # customer_name will be pulled from the order automatically


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class StaffResponseUpdate(BaseModel):
    """Schema for staff to respond to reviews"""
    staff_response: str


class Review(ReviewBase):
    id: int
    order_id: int
    sandwich_id: int
    customer_name: str
    review_date: datetime
    staff_response: Optional[str] = None
    response_date: Optional[datetime] = None
    sandwich: Optional[Sandwich] = None

    class ConfigDict:
        from_attributes = True


class ReviewSummary(BaseModel):
    """Schema for displaying review statistics per sandwich"""
    sandwich_id: int
    sandwich_name: str
    total_reviews: int
    average_rating: float
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int