from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from typing import List, Optional
from helper.respository.repo_server import (
    add_user,
    get_user_by_username_or_email,
    get_all_users,
    delete_user,
    verify_password,
)

app = FastAPI()


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


@app.post("/register")
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


@app.post("/login")
def login_user(credentials: UserLogin, response: Response):
    user = get_user_by_username_or_email(credentials.username_or_email)
    if user and verify_password(credentials.password, user[0]):
        # Tạo cookie để lưu trạng thái đăng nhập
        response.set_cookie(
            key="username_or_email", value=user[0], max_age=30 * 24 * 60 * 60
        )  # Cookie có hiệu lực trong 30 ngày
        return {"message": "Login successful."}
    else:
        raise HTTPException(
            status_code=401, detail="Invalid username/email or password."
        )


@app.get("/users", response_model=List[UserResponse])
def get_users(request: Request):
    # Kiểm tra cookie để tự động đăng nhập
    username = request.cookies.get("username")
    if username:
        # Nếu có cookie, coi như người dùng đã đăng nhập
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
    else:
        raise HTTPException(status_code=401, detail="Not logged in.")


@app.delete("/users/{username}")
def delete_user_api(username: str):
    delete_user(username)
    return {"message": f"User '{username}' deleted successfully."}


@app.post("/logout")
def logout_user(response: Response):
    # Xóa cookie khi đăng xuất
    response.delete_cookie(key="username")
    return {"message": "Logout successful."}
