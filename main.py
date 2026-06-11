from fastapi import FastAPI, UploadFile, File
import pdfplumber
import os
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
def home():
    return {"message": "AI Audit API Running"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    invoice_match = re.search(r"Invoice Number:\s*(.+)", text)
    vendor_match = re.search(r"Vendor:\s*(.+)", text)
    amount_match = re.search(r"Amount:\s*[₹Rs.\s]*([\d,]+)", text)
    date_match = re.search(r"Date:\s*(\d{2}/\d{2}/\d{4})", text)

    invoice = invoice_match.group(1).strip() if invoice_match else None
    vendor = vendor_match.group(1).strip() if vendor_match else None
    amount = amount_match.group(1).replace(",", "") if amount_match else None
    date = date_match.group(1) if date_match else None

    return {
        "invoice": invoice,
        "vendor": vendor,
        "amount": amount,
        "date": date
    }
