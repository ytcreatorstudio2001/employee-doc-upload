from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.api
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Simple password for admin
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})

@app.post("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "❌ Wrong password!"})

    # List employee folders from Cloudinary
    folders = cloudinary.api.sub_folders("employee_docs")['folders']

    employees = []
    for f in folders:
        folder_path = f['path']
        # List all files in this folder
        files = cloudinary.api.resources(type="upload", prefix=folder_path)['resources']
        file_links = {file['public_id'].split('/')[-1]: file['secure_url'] for file in files}
        employees.append({
            "name": folder_path.split('/')[-1],
            "files": file_links
        })

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "employees": employees})
