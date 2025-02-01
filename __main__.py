import os
import shutil
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.chat import router as chat_router


def delete_pycache(root_dir):
    for dirpath, dirnames, _ in os.walk(root_dir):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"Deleted: {pycache_path}")


# Tạo ứng dụng FastAPI chính
app = FastAPI()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các origin (hoặc thay bằng origin cụ thể)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm các router vào ứng dụng chính
app.include_router(auth_router, prefix="/auth")
app.include_router(chat_router, prefix="/chat")


# Mount thư mục chứa file HTML (nếu bạn muốn phục vụ các file tĩnh như CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


# Sử dụng Jinja2Templates để phục vụ file HTML
templates = Jinja2Templates(directory="templates")


# Endpoint để phục vụ trang login.html
@app.get("/chat", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse("chat/chat.html", {"request": request})


if __name__ == "__main__":
    # Xóa thư mục __pycache__
    delete_pycache(os.getcwd())
    # Xóa màn hình terminal
    os.system("cls" if os.name == "nt" else "clear")
    # Khởi động Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2401, reload=False, server_header=False)
