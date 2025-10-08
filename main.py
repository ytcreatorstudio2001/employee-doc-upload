from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import io
import zipfile

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =================== CONFIGURE CLOUDINARY ===================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# =================== EMPLOYEE UPLOAD ===================
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

    # Fetch employee folders
    try:
        folders = cloudinary.api.sub_folders("employee_docs")['folders']
    except Exception:
        folders = []

    employees = []
    for f in folders:
        folder_path = f['path']
        try:
            files = cloudinary.api.resources(type="upload", prefix=folder_path, resource_type="auto")['resources']
        except Exception:
            files = []
        file_links = {file['public_id'].split('/')[-1]: file['secure_url'] for file in files}
        employees.append({
            "name": folder_path.split('/')[-1],
            "folder_path": folder_path,
            "files": file_links
        })

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "employees": employees})

# =================== DOWNLOAD EMPLOYEE FOLDER ===================
@app.get("/download/{folder_name}")
async def download_folder(folder_name: str):
    folder_path = f"employee_docs/{folder_name}"
    try:
        files = cloudinary.api.resources(type="upload", prefix=folder_path, resource_type="auto")['resources']
    except Exception:
        return {"error": "Folder not found or empty."}

    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in files:
            # Download file from Cloudinary
            url = file['secure_url']
            public_id = file['public_id'].split('/')[-1]
            file_data = cloudinary.uploader.download(url)
            zip_file.writestr(public_id, file_data)

    zip_buffer.seek(0)
    return FileResponse(zip_buffer, media_type="application/zip", filename=f"{folder_name}.zip")
