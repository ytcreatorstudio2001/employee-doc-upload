from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import io
import zipfile
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =================== CLOUDINARY CONFIG ===================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# =================== ADMIN PASSWORD ===================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


# =================== EMPLOYEE UPLOAD PORTAL ===================
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


# =================== ADMIN PORTAL ===================
@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})

@app.post("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "❌ Wrong password!"})

    # List all resources under employee_docs
    try:
        resources = cloudinary.api.resources(type="upload", prefix="employee_docs")['resources']
    except Exception:
        resources = []

    # Organize files by employee folder
    employees_dict = {}
    for file in resources:
        parts = file['public_id'].split('/')
        if len(parts) >= 2:
            employee_folder = parts[1]  # "Name_AadharNumber"
            if employee_folder not in employees_dict:
                employees_dict[employee_folder] = []
            employees_dict[employee_folder].append({
                "file_name": parts[-1],
                "url": file['secure_url']
            })

    employees = [{"name": k, "files": v} for k, v in employees_dict.items()]

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "employees": employees})


# =================== BULK DOWNLOAD ===================
@app.get("/download/{employee_folder}")
async def download_employee_files(employee_folder: str):
    # Get all files in this folder
    try:
        resources = cloudinary.api.resources(type="upload", prefix=f"employee_docs/{employee_folder}")['resources']
    except Exception:
        resources = []

    if not resources:
        return {"error": "No files found for this employee."}

    # Create in-memory ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in resources:
            file_name = file['public_id'].split('/')[-1]
            # Download file content
            r = requests.get(file['secure_url'])
            zip_file.writestr(file_name, r.content)

    zip_buffer.seek(0)
    return FileResponse(
        zip_buffer,
        media_type="application/zip",
        filename=f"{employee_folder}.zip"
    )
