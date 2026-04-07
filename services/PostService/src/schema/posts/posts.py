from pydantic import BaseModel, field_validator
from uuid import UUID

MAX_TAGS = 5


class CreatePostRequest(BaseModel):
    body: str
    title: str
    image_link: str | None = None
    tags: list[str]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        tags = [t.strip().lower() for t in v if t.strip()]
        if len(tags) == 0:
            raise ValueError("at least 1 tag is required")
        if len(tags) > MAX_TAGS:
            raise ValueError(f"at most {MAX_TAGS} tags are allowed")
        return tags


class PostResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    user_name: str
    user_avatar: str | None = None
    body: str
    title: str
    image_link: str | None = None
    like_count: int = 0
    comment_count: int = 0
    tags: list[str] = []


class PatchPostRequest(BaseModel):
    edited_by: str = ""
    title: str | None = None
    body: str | None = None
    image_link: str | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        tags = [t.strip().lower() for t in v if t.strip()]
        if len(tags) == 0:
            raise ValueError("at least 1 tag is required")
        if len(tags) > MAX_TAGS:
            raise ValueError(f"at most {MAX_TAGS} tags are allowed")
        return tags


class DeletePostRequest(BaseModel):
    post_id: UUID
    user_id: UUID


class SearchPostRequest(BaseModel):
    query: str


class SearchPostItem(BaseModel):
    post_id: UUID
    title: str
    body: str
    offset: int = 0


class SearchPostsResponse(BaseModel):
    items: list[SearchPostItem]  

class LikedByResponse(BaseModel):
    users: list[str]

class FeedPostResponse(BaseModel):
    posts : list[PostResponse]