from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.uploader
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Cloudinary config from Railway environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

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
    folder = "employee_docs"

    # file renaming rules
    aadhar_name = f"{aadhar_password}_{name}_{aadhar_number}_Aadhar"
    your_photo_name = f"{name}_{aadhar_number}_Photo"
    nominee_photo_name = f"{name}_{aadhar_number}_{nominee_relation}"
    bank_passbook_name = f"{name}_{aadhar_number}_Bank"

    uploads = {}

    def upload_to_cloudinary(file, filename):
        return cloudinary.uploader.upload(
            file.file,
            folder=folder,
            public_id=filename,
            overwrite=True,
            resource_type="image"
        )["secure_url"]

    uploads["Aadhar Card"] = upload_to_cloudinary(aadhar_card, aadhar_name)
    uploads["Your Photo"] = upload_to_cloudinary(your_photo, your_photo_name)
    uploads["Nominee Photo"] = upload_to_cloudinary(nominee_photo, nominee_photo_name)
    uploads["Bank Passbook"] = upload_to_cloudinary(bank_passbook, bank_passbook_name)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": "✅ Files uploaded successfully!",
        "uploads": uploads
    })
