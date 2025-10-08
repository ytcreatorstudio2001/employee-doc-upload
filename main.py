from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.api
import requests
import io
import zipfile
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ===========================
# Admin Login & Dashboard
# ===========================
@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})

@app.post("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "❌ Wrong password!"})

    # List employee folders
    try:
        folders = cloudinary.api.sub_folders("employee_docs")['folders']
    except Exception:
        folders = []

    employees = []
    for f in folders:
        folder_path = f['path']
        try:
            files = cloudinary.api.resources(type="upload", prefix=folder_path)['resources']
        except Exception:
            files = []
        file_links = {file['public_id'].split('/')[-1]: file['secure_url'] for file in files}
        employees.append({
            "name": folder_path.split('/')[-1],
            "folder_path": folder_path,
            "files": file_links
        })

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "employees": employees})

# ===========================
# Download Employee Folder as ZIP
# ===========================
@app.get("/download/{folder_name}")
async def download_employee_folder(folder_name: str):
    folder_path = f"employee_docs/{folder_name}"
    
    try:
        files = cloudinary.api.resources(type="upload", prefix=folder_path)['resources']
    except Exception:
        files = []

    if not files:
        return {"error": "No files found in this folder."}

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in files:
            file_url = file['secure_url']
            file_name = file['public_id'].split('/')[-1]
            # Download file content
            r = requests.get(file_url)
            zip_file.writestr(file_name, r.content)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={folder_name}.zip"}
    )
