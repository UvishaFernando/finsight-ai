from pydantic import BaseModel, Field


class CategorySuggestionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)


class CategorySuggestionResponse(BaseModel):
    category: str
