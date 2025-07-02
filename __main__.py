import os
import shutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from config.settings import CORS_SETTINGS


def delete_pycache(root_dir):
    """Remove all __pycache__ directories."""
    for dirpath, dirnames, _ in os.walk(root_dir):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"Deleted: {pycache_path}")

app = FastAPI()
app.add_middleware(CORSMiddleware, **CORS_SETTINGS)
app.include_router(auth_router)
app.include_router(chat_router)
app.mount("/templates/static", StaticFiles(directory="templates/static"), name="templates/static")
app.mount("/storage", StaticFiles(directory="/home/nguyentrung/Documents/ollama_api/storage"), name="storage")

templates = Jinja2Templates(directory="templates")

@app.get("/chat", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Serve chat page."""
    response = templates.TemplateResponse("chat/chat.html", {"request": request})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """Serve login page."""
    response = templates.TemplateResponse("authentication/login.html", {"request": request})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/test", response_class=HTMLResponse)
async def get_test(request: Request):
    """Serve test page."""
    response = templates.TemplateResponse("test/index.html", {"request": request})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/", response_class=RedirectResponse)
async def redirect_to_chat():
    """Redirect root to chat page."""
    return RedirectResponse(url="/chat", status_code=302)

if __name__ == "__main__":
    # Chạy clean.sh trước khi chạy main
    os.system("bash clean.sh")
    delete_pycache(os.getcwd())
    os.system("cls" if os.name == "nt" else "clear")
    uvicorn.run(app, host="0.0.0.0", port=2401, reload=False, server_header=False)
