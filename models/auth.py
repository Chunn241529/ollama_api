from pydantic import BaseModel

class UserRegistration(BaseModel):
    username: str
    password: str
    verify_code: str
    phone: str
    email: str
    full_name: str
    avatar: str

class UserLogin(BaseModel):
    username_or_email: str = "admin"
    password: str = "admin"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    avatar: str
    db_name: str

class GetUserByEmail(BaseModel):
    id: int
    full_name: str
    email: str
    avatar: str
    phone: int
    db_name: str
