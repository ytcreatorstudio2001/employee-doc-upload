from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# Load environment variables (Railway will provide them)
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@app.get("/", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def upload_docs(
    request: Request,
    name: str = Form(...),
    aadhar_number: str = Form(...),
    nominee_name: str = Form(...),
    nominee_relation: str = Form(...),
    aadhar_password: str = Form(...),
    aadhar_card: UploadFile = File(...),
    your_photo: UploadFile = File(...),
    nominee_photo: UploadFile = File(...),
    bank_passbook: UploadFile = File(...),
):
    safe_name = name.replace(" ", "_")
    safe_relation = nominee_relation.replace(" ", "_")

    # Rename files based on your logic
    renamed_files = {
        aadhar_card: f"{aadhar_password}_{safe_name}_{aadhar_number}{os.path.splitext(aadhar_card.filename)[1]}",
        your_photo: f"{safe_name}_{aadhar_number}_Photo{os.path.splitext(your_photo.filename)[1]}",
        nominee_photo: f"{safe_name}_{aadhar_number}_{safe_relation}{os.path.splitext(nominee_photo.filename)[1]}",
        bank_passbook: f"{safe_name}_{aadhar_number}_Bank{os.path.splitext(bank_passbook.filename)[1]}",
    }

    uploaded_links = {}

    for file_obj, new_name in renamed_files.items():
        upload_result = cloudinary.uploader.upload(
            file_obj.file,
            public_id=f"employee_docs/{new_name}",
            overwrite=True,
            resource_type="auto"
        )
        uploaded_links[new_name] = upload_result["secure_url"]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": f"✅ Documents uploaded successfully for {name}!",
            "urls": uploaded_links,
        },
    )
