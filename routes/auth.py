from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import List
from datetime import timedelta
from models.auth import UserRegistration, UserLogin, UserResponse, GetUserByEmail
from dependencies.auth import verify_token, create_access_token
from config.settings import ACCESS_TOKEN_EXPIRE_MINUTES
from services.repository.repo_server import (
    add_user,
    get_password_by_username_or_email,
    get_user_by_email,
    get_db_user_by_username_or_email,
    get_all_users,
    delete_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login_user(credentials: UserLogin):
    """Authenticate user and return JWT token."""
    user = get_password_by_username_or_email(credentials.username_or_email)
    if user and verify_password(credentials.password, user[0]):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": credentials.username_or_email},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username/email or password.")

@router.post("/register")
def register_user(user: UserRegistration):
    """Register a new user."""
    try:
        add_user(user.dict())
        return {"message": f"User '{user.username}' registered successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/db")
def get_db_path(
    username_or_email: str = Query(..., description="Username or email of the user")
):
    """Retrieve database path for a user."""
    import time
    start_time = time.time()
    db_path = get_db_user_by_username_or_email(username_or_email)
    end_time = time.time()
    print(f"DB Query Time: {end_time - start_time:.3f} sec")
    if db_path is None:
        raise HTTPException(status_code=404, detail="Database path not found for the user.")
    return {"db_path": db_path[0]}

@router.get("/users", response_model=List[UserResponse])
def get_users(username: dict = Depends(verify_token)):
    """List all users (requires authentication)."""
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

@router.get("/users/{email}", response_model=GetUserByEmail)
def get_user_by_email_route(email: str, _: dict = Depends(verify_token)):
    """Retrieve user by email (requires authentication)."""
    user = get_user_by_email(email)
    if user and len(user) >= 5:
        return GetUserByEmail(
            id=user[0],
            full_name=user[2],
            email=user[3],
            avatar=user[4],
            phone=user[5],
            db_name=user[6],
        )
    raise HTTPException(status_code=404, detail="User not found.")

@router.delete("/users/{username}")
def delete_user_api(username: str, _: dict = Depends(verify_token)):
    """Delete a user (requires authentication)."""
    delete_user(username)
    return {"message": f"User '{username}' deleted successfully."}

@router.post("/logout")
def logout_user(response: Response):
    """Log out user by clearing authorization cookie."""
    response.delete_cookie(key="Authorization")
    return {"message": "Logout successful."}
