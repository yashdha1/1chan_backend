from pydantic import BaseModel
from uuid import UUID


class PostRequest(BaseModel):
    body: str
    title: str
    image_link: str | None = None


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


class PatchPostRequest(BaseModel):
    edited_by: str = ""
    title: str | None = None
    body: str | None = None
    image_link: str | None = None


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
