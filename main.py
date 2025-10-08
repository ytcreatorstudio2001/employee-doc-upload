from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import io
import zipfile
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Make sure templates folder exists

# =================== CLOUDINARY CONFIG ===================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# =================== ADMIN PASSWORD ===================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# =========================== EMPLOYEE UPLOAD ===========================
@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_files(
    request: Request,
    name: str = Form(...),
    aadhar_number: str = Form(...),
    nominee_name: str = Form(...),
    nominee_relation: str = Form(...),
    aadhar_password: str = Form(...),
    aadhar_card: UploadFile = File(...),
    your_photo: UploadFile = File(...),
    nominee_photo: UploadFile = File(...),
    bank_passbook: UploadFile = File(...)
):
    folder = f"employee_docs/{name}_{aadhar_number}"

    # File renaming
    renamed_files = {
        "Aadhar Card": f"{aadhar_password}_{name}_{aadhar_number}_Aadhar",
        "Your Photo": f"{name}_{aadhar_number}_Photo",
        "Nominee Photo": f"{name}_{aadhar_number}_{nominee_relation}",
        "Bank Passbook": f"{name}_{aadhar_number}_Bank"
    }

    file_objects = {
        "Aadhar Card": aadhar_card,
        "Your Photo": your_photo,
        "Nominee Photo": nominee_photo,
        "Bank Passbook": bank_passbook
    }

    uploaded_links = {}
    for label, file_obj in file_objects.items():
        upload_result = cloudinary.uploader.upload(
            file_obj.file,
            folder=folder,
            public_id=renamed_files[label],
            overwrite=True,
            resource_type="auto"
        )
        uploaded_links[label] = upload_result["secure_url"]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"✅ Files uploaded successfully for {name}!",
        "uploads": uploaded_links
    })

# =========================== ADMIN PORTAL ===========================
@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})

@app.post("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "❌ Wrong password!"})

    # Fetch all files under employee_docs
    try:
        all_files = cloudinary.api.resources(type="upload", prefix="employee_docs")['resources']
    except Exception:
        all_files = []

    # Group files by employee folder
    folders_dict = {}
    for file in all_files:
        parts = file['public_id'].split('/')
        if len(parts) < 2:
            continue
        folder_name = parts[1]  # employee folder
        if folder_name not in folders_dict:
            folders_dict[folder_name] = []
        folders_dict[folder_name].append({
            "file_name": parts[-1],
            "url": file['secure_url']
        })

    employees = []
    for folder, files in folders_dict.items():
        employees.append({
            "name": folder,
            "files": {f['file_name']: f['url'] for f in files}
        })

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "employees": employees})

# =========================== DOWNLOAD EMPLOYEE FOLDER AS ZIP ===========================
@app.get("/download/{employee_folder}")
async def download_employee_folder(employee_folder: str):
    try:
        all_files = cloudinary.api.resources(type="upload", prefix=f"employee_docs/{employee_folder}")['resources']
    except Exception:
        all_files = []

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in all_files:
            file_name = file['public_id'].split('/')[-1]
            file_url = file['secure_url']
            response = requests.get(file_url)
            zip_file.writestr(file_name, response.content)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={employee_folder}.zip"}
    )
