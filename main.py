# main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import cloudinary
import cloudinary.api

# =================== CONFIGURE CLOUDINARY ===================
cloudinary.config(
    cloud_name="YOUR_CLOUD_NAME",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET"
)

# =================== FASTAPI SETUP ===================
app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Make sure this folder exists

# =================== FUNCTION TO FETCH FOLDERS ===================
def get_cloudinary_folders():
    try:
        response = cloudinary.api.folders()  # fetch all root folders
        folders = response.get('folders', [])
        return [f['name'] for f in folders]
    except cloudinary.api.Error as e:
        print("Cloudinary API Error:", e)
        return []

# =================== DASHBOARD ROUTE ===================
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    folders = get_cloudinary_folders()  # fetch folders
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "username": "Admin",
        "folders": folders
    })
