from pydantic import BaseModel
from typing import List, Optional


class Subcategory(BaseModel):
    id: str
    name: str
    thumbnail: Optional[str] = None


class Category(BaseModel):
    id: str
    name: str
    thumbnail: Optional[str] = None
    sub_categories: List[Subcategory] = []


class CategoryCreate(BaseModel):
    name: str


class SubcategoryCreate(BaseModel):
    category_id: str
    name: str
