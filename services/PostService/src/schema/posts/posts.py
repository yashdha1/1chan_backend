from pydantic import BaseModel
from uuid import UUID 


class PostRequest(BaseModel): # to make the post :
    body : str
    title : str 
    image_link : str | None = None

class PostResponse(BaseModel):
    post_id : UUID
    user_id : UUID
    user_name : str 
    user_avatar : str | None = None
    body : str 
    title : str
    image_link : str | None = None
    like_count : int = 0
    comment_count : int = 0

# patch the posts
class PatchPostRequest(BaseModel) :
    edited_by : str
    post_id : UUID
    title : str | None = None
    body : str | None = None
    image_link : str | None = None

# delete the posts
class DeletePostRequest(BaseModel) :
    post_id : UUID
    user_id : UUID


class SearchPostRequest(BaseModel) : 
    query : str

class SearchPostResponse(BaseModel) :
    post_id : UUID
    title : str
    body : str
    offset : int  # the offset of the search result: by this factor : 
