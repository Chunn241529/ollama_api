from typing import List
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Query, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt  # Sử dụng PyJWT
from helper.respository.repo_server import (
    add_user,
    get_user_by_username_or_email,
    get_db_user_by_username_or_email,
    get_all_users,
    delete_user,
    verify_password,
)

router = APIRouter()


# Khóa bí mật để ký JWT
SECRET_KEY = "chungpt_2401"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Models
class UserRegistration(BaseModel):
    username: str
    password: str
    verify_code: str
    phone: str
    email: str
    full_name: str
    avatar: str


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    avatar: str


# Hàm tạo JWT
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register")
def register_user(user: UserRegistration):
    """
    Register a new user. Check if username or email already exists.
    """
    try:
        # Gọi hàm add_user từ repo_server
        add_user(user.dict())
        return {"message": f"User '{user.username}' registered successfully."}
    except ValueError as e:
        # Trả về lỗi nếu username/email đã tồn tại
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login_user(credentials: UserLogin):
    user = get_user_by_username_or_email(credentials.username_or_email)
    if user and verify_password(credentials.password, user[0]):
        # Tạo JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user[0]}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    else:
        raise HTTPException(
            status_code=401, detail="Invalid username/email or password."
        )


@router.post("/token")
def login_user(credentials: UserLogin):
    user = get_user_by_username_or_email(credentials.username_or_email)
    if user and verify_password(credentials.password, user[0]):
        # Tạo JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user[0]}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    else:
        raise HTTPException(
            status_code=401, detail="Invalid username/email or password."
        )


@router.get("/db")
def get_db_path(
    username_or_email: str = Query(..., description="Username or email of the user")
):
    db_path = get_db_user_by_username_or_email(username_or_email)
    if db_path is None:
        raise HTTPException(
            status_code=404, detail="Database path not found for the user."
        )
    return {"db_path": db_path[0]}


@router.get("/users", response_model=List[UserResponse])
def get_users(request: Request):
    # Kiểm tra JWT để xác thực người dùng
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    try:
        token = token.split("Bearer ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    # Lấy danh sách người dùng
    users = get_all_users()
    return [
        UserResponse(
            id=user[0],
            username=user[1],
            email=user[2],
            full_name=user[3],
            avatar=user[4],
        )
        for user in users
    ]


@router.delete("/users/{username}")
def delete_user_api(username: str):
    delete_user(username)
    return {"message": f"User '{username}' deleted successfully."}


@router.post("/logout")
def logout_user(response: Response):
    # Xóa cookie khi đăng xuất (nếu có)
    response.delete_cookie(key="username")
    return {"message": "Logout successful."}
