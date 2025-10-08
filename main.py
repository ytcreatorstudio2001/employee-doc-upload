from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ========================
# Cloudinary Configuration
# ========================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Admin password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


# ===========================
# Employee Upload Portal
# ===========================
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
        try:
            upload_result = cloudinary.uploader.upload(
                file_obj.file,
                folder=folder,
                public_id=renamed_files[label],
                overwrite=True,
                resource_type="auto"
            )
            uploaded_links[label] = upload_result.get("secure_url", "❌ No URL returned")
        except Exception as e:
            uploaded_links[label] = f"❌ Failed to upload: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"✅ Files uploaded successfully for {name}!",
        "uploads": uploaded_links
    })


# ===========================
# Admin Portal
# ===========================
@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})

@app.post("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "❌ Wrong password!"})

    employees = []

    try:
        # List employee folders safely
        folders_resp = cloudinary.api.sub_folders("employee_docs")
        folders = folders_resp.get('folders', [])
        print("Folders fetched:", folders)
    except Exception as e:
        print("Error fetching folders:", e)
        folders = []

    for f in folders:
        folder_path = f.get('path', '')
        file_links = {}

        try:
            resources_resp = cloudinary.api.resources(type="upload", prefix=folder_path)
            resources = resources_resp.get('resources', [])
            print(f"Resources in {folder_path}:", resources)
            for file in resources:
                filename = file['public_id'].split('/')[-1]
                file_links[filename] = file.get('secure_url', '#')
        except Exception as e:
            print(f"Error fetching resources in {folder_path}:", e)
            file_links = {}

        employees.append({
            "name": folder_path.split('/')[-1] if folder_path else "Unknown",
            "files": file_links
        })

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "employees": employees})
