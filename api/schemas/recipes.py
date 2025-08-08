from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .resources import Resource
from .sandwiches import Sandwich


class RecipeBase(BaseModel):
    amount: int
    unit: str = "piece"  # "piece", "oz", "cup", "slice", etc.


class RecipeCreate(RecipeBase):
    sandwich_id: int
    resource_id: int


class RecipeUpdate(BaseModel):
    sandwich_id: Optional[int] = None
    resource_id: Optional[int] = None
    amount: Optional[int] = None
    unit: Optional[str] = None


class Recipe(RecipeBase):
    id: int
    sandwich_id: int
    resource_id: int
    sandwich: Optional[Sandwich] = None
    resource: Optional[Resource] = None

    class ConfigDict:
        from_attributes = True