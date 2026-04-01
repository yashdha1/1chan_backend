from pydantic import BaseModel
from uuid import UUID


class CommentResponse(BaseModel):
    comment_id: UUID
    post_id: UUID
    parent_id: UUID | None = None
    user_id: UUID
    user_name: str
    user_avatar: str | None = None
    body: str
    like_count: int = 0
    created_at: str | None = None


class CommentPostRequest(BaseModel):
    post_id: UUID
    parent_id: UUID | None = None
    body: str


class CommentGetRequest(BaseModel):
    post_id: UUID
    parent_id: UUID | None = None
    user_id: UUID
    user_name: str
    user_avatar: str | None = None
    body: str
    like_count: int
    created_at: str


class CommentLikeRequest(BaseModel):
    comment_id: UUID


class CommentUnlikeRequest(BaseModel):
    comment_id: UUID


class CommentDeleteRequest(BaseModel):
    comment_id: UUID
    user_id: UUID
