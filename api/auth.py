import os
from typing import List
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt  # PyJWT
from service.respository.repo_server import (
    add_user,
    get_user_by_username_or_email,
    get_db_user_by_username_or_email,
    get_all_users,
    delete_user,
    verify_password,
)

router = APIRouter()

oauth2_scheme = HTTPBearer()

import secrets


def generate_secret_key(length=50):
    return secrets.token_urlsafe(length)


SECRET_KEY = generate_secret_key()
load_dotenv()
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


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
    username_or_email: str = "admin"
    password: str = "admin"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    avatar: str
    db_name: str


# Utility to create JWT
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Middleware to verify JWT
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Payload:", payload)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload.")
        return {"username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")


@router.post("/login")
def login_user(credentials: UserLogin):
    user = get_user_by_username_or_email(credentials.username_or_email)
    if user and verify_password(credentials.password, user[0]):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": credentials.username_or_email},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=401, detail="Invalid username/email or password."
        )


# Routes
@router.post("/register")
def register_user(user: UserRegistration):
    try:
        add_user(user.dict())
        return {"message": f"User '{user.username}' registered successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


import time


@router.get("/db")
def get_db_path(
    username_or_email: str = Query(..., description="Username or email of the user")
):
    start_time = time.time()
    db_path = get_db_user_by_username_or_email(username_or_email)
    end_time = time.time()
    print(f"DB Query Time: {end_time - start_time:.3f} sec")

    if db_path is None:
        raise HTTPException(
            status_code=404, detail="Database path not found for the user."
        )

    return {"db_path": db_path[0]}


@router.get("/users", response_model=List[UserResponse])
def get_users(username: str = Depends(verify_token)):
    users = get_all_users()
    return [
        UserResponse(
            id=user[0],
            username=user[1],
            email=user[2],
            full_name=user[3],
            avatar=user[4],
            db_name=user[5],
        )
        for user in users
    ]


@router.delete("/users/{username}")
def delete_user_api(username: str, _: str = Depends(verify_token)):
    delete_user(username)
    return {"message": f"User '{username}' deleted successfully."}


@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(key="Authorization")
    return {"message": "Logout successful."}
