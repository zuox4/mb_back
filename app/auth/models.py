from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserLogin(BaseModel):
    email: str
    external_id: int

class UserCreate(BaseModel):
    email: str
    external_id: int
    display_name: Optional[str] = None

class RegisterRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    token: str

class GoogleUserInfo(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    email: str
    password: str

class VerifyEmailRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    email: str
    display_name: Optional[str] = None
    roles: Optional[list] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
