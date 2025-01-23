from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from helper.respository.repo_server import UserRepository
import random

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "123"

user_repo = UserRepository("server.sqlite3")


class User(BaseModel):
    username: str
    password: str
    email: str
    verify_code: str = ""
    phone: str = ""
    full_name: str = ""
    avatar: str = ""


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = user_repo.get_user(payload["username"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_verify_code():
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


@app.post("/register")
def register(user: User):
    hashed_password = generate_password_hash(user.password, method="pbkdf2:sha256")
    verify_code = generate_verify_code()
    user_repo.add_user(
        username=user.username,
        password=hashed_password,
        verify_code=verify_code,
        phone=user.phone,
        email=user.email,
        db_name=f"{user.username}.db",
        full_name=user.full_name,
        avatar=user.avatar,
    )
    return {"message": "Registered successfully!", "verify_code": verify_code}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_repo.get_user(form_data.username)
    if not user or not check_password_hash(user[2], form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = jwt.encode(
        {
            "username": user[1],
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(minutes=30),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/user")
def get_user(current_user: dict = Depends(get_current_user)):
    user_data = {
        "id": current_user[0],
        "username": current_user[1],
        "email": current_user[2],
        "full_name": current_user[3],
        "avatar": current_user[4],
    }
    return {"user": user_data}


@app.delete("/delete_user")
def delete_user(current_user: dict = Depends(get_current_user)):
    user_repo.delete_user(current_user[1])
    return {"message": "User deleted successfully!"}
