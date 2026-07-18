import json
from typing import List, Any, Dict, Optional, Tuple
from dataclasses import dataclass, field

@dataclass(eq=False)
class SearchItem:
    title: str
    url: str
    image_url: Optional[str] = None
    embedding: Optional[List[float]] = None
    similarity_score: Optional[float] = None
    rerank_score: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SearchItem":
        title = d.get("title")
        url = d.get("url")
        image_url = d.get("image_url")
        embedding = d.get("embedding")
        data = {k: v for k, v in d.items() if k not in {"title", "url", "image_url", "embedding"}}
        return SearchItem(title=title, url=url, image_url=image_url, embedding=embedding, data=data)

    def to_dict(self) -> Dict[str, Any]:
        base = {"title": self.title, "url": self.url}
        if self.image_url is not None:
            base["image_url"] = self.image_url
        if self.embedding is not None:
            base["embedding"] = self.embedding
        base.update(self.data)
        return base

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "SearchItem":
        return SearchItem.from_dict(json.loads(s))

@dataclass
class RerankFeedback:
    item_url: str
    feedback_type: str
    concept: str

    @staticmethod
    def from_row(row: Tuple) -> "RerankFeedback":
        if len(row) == 3:
            return RerankFeedback(item_url=row[0], feedback_type=row[1], concept=row[2])
        else:
            return RerankFeedback(item_url=row[0], feedback_type=row[1])

@dataclass
class QueryDTO:
    id: int
    search_keyword: str
    query_params: Optional[str] = None

    @staticmethod
    def from_row(row: Tuple) -> "QueryDTO":
        return QueryDTO(id=row[0], search_keyword=row[1], query_params=row[2])

@dataclass
class UserUpload:
    id: int
    image_path: str

    @staticmethod
    def from_row(row: Tuple) -> "UserUpload":
        return UserUpload(id=row[0], image_path=row[1])

