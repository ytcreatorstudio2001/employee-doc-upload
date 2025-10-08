from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.api
import cloudinary.uploader
import os
import io
import zipfile
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Admin password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


# ==========================
# Admin Login Page
# ==========================
@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})


@app.post("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "❌ Wrong password!"})

    # Fetch employee folders
    try:
        folders_data = cloudinary.api.sub_folders("employee_docs")['folders']
    except cloudinary.api.Error:
        folders_data = []

    folders = [{"name": f['name'], "path": f['path']} for f in folders_data]

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "folders": folders})


# ==========================
# View Folder Files
# ==========================
@app.get("/admin/folder/{folder_name}", response_class=HTMLResponse)
async def view_folder(request: Request, folder_name: str):
    folder_path = f"employee_docs/{folder_name}"
    try:
        resources = cloudinary.api.resources(
            type="upload",
            prefix=folder_path,
            resource_type="auto",
            max_results=500
        )['resources']
    except cloudinary.api.Error:
        resources = []

    files = [{"name": r['public_id'].split('/')[-1], "url": r['secure_url']} for r in resources]

    return templates.TemplateResponse("folder_view.html", {
        "request": request,
        "folder_name": folder_name,
        "files": files
    })


# ==========================
# Download Single File
# ==========================
@app.get("/download/file/")
async def download_file(file_url: str, file_name: str):
    resp = requests.get(file_url)
    return StreamingResponse(io.BytesIO(resp.content), media_type="application/octet-stream", headers={
        "Content-Disposition": f"attachment; filename={file_name}"
    })


# ==========================
# Download Entire Folder as ZIP
# ==========================
@app.get("/download/folder/{folder_name}")
async def download_folder(folder_name: str):
    folder_path = f"employee_docs/{folder_name}"
    try:
        resources = cloudinary.api.resources(
            type="upload",
            prefix=folder_path,
            resource_type="auto",
            max_results=500
        )['resources']
    except cloudinary.api.Error:
        resources = []

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, mode="w") as zf:
        for r in resources:
            file_resp = requests.get(r['secure_url'])
            file_name = r['public_id'].split('/')[-1]
            zf.writestr(file_name, file_resp.content)

    zip_io.seek(0)
    return StreamingResponse(zip_io, media_type="application/zip", headers={
        "Content-Disposition": f"attachment; filename={folder_name}.zip"
    })
