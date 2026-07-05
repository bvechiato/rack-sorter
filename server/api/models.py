from pydantic import BaseModel

class FetchInitialRequest(BaseModel):
    uploadId: int
    keyword: str
    selectedSizes: str
    selectedCategory: str
    selectedColors: str
    maxPrice: str
    selectedConditions: str

class ItemResponse(BaseModel):
    title: str
    url: str
    image_url: str
    similarity_score: float

class FetchInitialResponse(BaseModel):
    pool: list[ItemResponse]

class AnalyseResponse(BaseModel):
    archetype: str
    classified_tags: list[str]
    colour_archetype: str
    colour_classified_tags: list[str]
    category_archetype: str

class AnalyseAnchorImageResponse(BaseModel):
    upload_id: int
    analysis: AnalyseResponse
