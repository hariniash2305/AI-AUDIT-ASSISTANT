from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import shutil
import os
import re

app = FastAPI()

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "AI Audit Assistant Running"}


# ----------------------------
# Helper Function
# ----------------------------
def extract_pattern(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1).strip()

    return None


# ----------------------------
# Invoice Extraction
# ----------------------------
def extract_invoice_data(text):
    return {
        "invoice_number": extract_pattern(
            text,
            [
                r"Invoice\s*Number[:\s]*([A-Z0-9\-]+)",
                r"Invoice\s*No\.?[:\s]*([A-Z0-9\-]+)",
                r"Invoice\s*#[:\s]*([A-Z0-9\-]+)"
            ]
        ),

        "vendor": extract_pattern(
            text,
            [
                r"Vendor[:\s]*(.+)",
                r"Supplier[:\s]*(.+)"
            ]
        ),

        "amount": extract_pattern(
            text,
            [
                r"Total\s*Amount[:\s₹]*([\d,\.]+)",
                r"Amount[:\s₹]*([\d,\.]+)"
            ]
        ),

        "date": extract_pattern(
            text,
            [
                r"Date[:\s]*(\d{2}/\d{2}/\d{4})",
                r"Date[:\s]*(\d{2}-\d{2}-\d{4})"
            ]
        ),

        "gst_number": extract_pattern(
            text,
            [
                r"GST(?:IN)?[:\s]*([A-Z0-9]+)"
            ]
        ),

        "po_number": extract_pattern(
            text,
            [
                r"PO\s*Number[:\s]*([A-Z0-9\-]+)",
                r"PO\s*No\.?[:\s]*([A-Z0-9\-]+)"
            ]
        ),

        "tax": extract_pattern(
            text,
            [
                r"Tax[:\s₹]*([\d,\.]+)"
            ]
        )
    }


# ----------------------------
# Purchase Order Extraction
# ----------------------------
def extract_po_data(text):
    return {
        "po_number": extract_pattern(
            text,
            [
                r"PO\s*Number[:\s]*([A-Z0-9\-]+)",
                r"Purchase\s*Order\s*No\.?[:\s]*([A-Z0-9\-]+)"
            ]
        ),

        "vendor": extract_pattern(
            text,
            [
                r"Vendor[:\s]*(.+)",
                r"Supplier[:\s]*(.+)"
            ]
        ),

        "amount": extract_pattern(
            text,
            [
                r"Approved\s*Amount[:\s₹]*([\d,\.]+)",
                r"Amount[:\s₹]*([\d,\.]+)"
            ]
        ),

        "date": extract_pattern(
            text,
            [
                r"Date[:\s]*(\d{2}/\d{2}/\d{4})",
                r"Date[:\s]*(\d{2}-\d{2}-\d{4})"
            ]
        )
    }


# ----------------------------
# Detect Document Type
# ----------------------------
def detect_document_type(text):

    text_lower = text.lower()

    if "purchase order" in text_lower:
        return "purchase_order"

    return "invoice"


# ----------------------------
# Upload Endpoint
# ----------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    document_type = detect_document_type(text)

    if document_type == "purchase_order":
        extracted_data = extract_po_data(text)
    else:
        extracted_data = extract_invoice_data(text)

    return {
        "filename": file.filename,
        "document_type": document_type,
        "data": extracted_data
    }