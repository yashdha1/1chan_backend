from pydantic import BaseModel
from typing import List, Literal
from uuid import UUID


class TagInsert(BaseModel):
    tag: str


class PostViewedUnit(BaseModel):
    post_id: int


class PostsViewed(BaseModel):
    posts: list[PostViewedUnit]


class PostTagAdd(BaseModel):
    post_id: str
    tags: List[str]


class UpdatePostTags(BaseModel):
    tags: list[str]
    op: str  # like, dislike or comment


class GenerateFeed(BaseModel):
    user_id : UUID 


class FeedResponse(BaseModel):
    post_ids: list[UUID]
    has_more: bool