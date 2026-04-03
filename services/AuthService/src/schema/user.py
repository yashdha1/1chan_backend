from pydantic import BaseModel
from uuid import UUID
from pydantic.fields import Field


class UserRegistrationRequest(BaseModel):
    username: str
    password: str = Field(min_length=8, max_length=128)
    bio: str
    avatar: str
    role: str


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    """returning both in the registration and the login"""

    access_token: str
    refresh_token: str


class UserOut(BaseModel):
    id: UUID
    username: str
    bio: str
    avatar: str
    role: str
    is_active: bool


class Profile(BaseModel):
    user: UserOut


class ProfileUpdateRequest(BaseModel):
    bio: str
    avatar: str
