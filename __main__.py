import os
import shutil
import uvicorn
from fastapi import FastAPI
from api.chat import app as chat_app
from api.auth import app as auth_app
from fastapi.middleware.cors import CORSMiddleware

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

# Mount các ứng dụng con
app.mount("/chat", chat_app)
app.mount("/auth", auth_app)

if __name__ == "__main__":
    # Xóa thư mục __pycache__
    delete_pycache(os.getcwd())
    # Xóa màn hình terminal
    os.system("cls" if os.name == "nt" else "clear")
    # Khởi động Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2401, reload=False)