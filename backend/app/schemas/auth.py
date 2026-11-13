from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    # bcrypt only uses the first 72 bytes, so we cap the length
    password: str = Field(min_length=8, max_length=72)
    skills: list[str] = Field(default_factory=list)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    name: str
    skills: list[str]
    created_at: datetime  # no password field: that's the point of a separate "out" schema


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"