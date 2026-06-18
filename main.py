from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import shutil
import os
import re
import traceback

from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base

import models
from models import Invoice, PurchaseOrder, AuditFinding

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Audit Assistant")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

# ====================== HELPERS ======================
def extract_pattern(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def detect_document_type(text: str):
    lower = text.lower()
    
    invoice_keywords = ["invoice", "bill no", "tax invoice", "gst invoice", "invoice number"]
    po_keywords = ["purchase order", "purchaseorder", "po number", "approved po"]
    
    if any(kw in lower for kw in invoice_keywords):
        return "invoice"
    if any(kw in lower for kw in po_keywords):
        return "purchase_order"
    
    return "invoice"  # default

def extract_invoice_data(text):
    return {
        "invoice_number": extract_pattern(text, [r"Invoice\s*Number[:\s]*([A-Z0-9\-]+)", r"Invoice\s*No\.?[:\s]*([A-Z0-9\-]+)", r"Bill\s*No\.?[:\s]*([A-Z0-9\-]+)"]),
        "vendor": extract_pattern(text, [r"Vendor[:\s]*(.+?)(?=\s*(?:GST|PO|Date|Total|$))", r"Supplier[:\s]*(.+?)(?=\s*(?:GST|PO|Date|$))", r"From[:\s]*(.+?)(?=\s*(?:GST|PO|$))"]),
        "amount": extract_pattern(text, [r"Total\s*Amount[:\s₹]*([\d,\.]+)", r"Grand\s*Total[:\s₹]*([\d,\.]+)", r"Amount[:\s₹]*([\d,\.]+)", r"₹\s*([\d,\.]+)"]),
        "date": extract_pattern(text, [r"Date[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})"]),
        "gst_number": extract_pattern(text, [r"GST(?:IN)?[:\s]*([A-Z0-9]+)"]),
        "po_number": extract_pattern(text, [r"PO\s*Number[:\s]*([A-Z0-9\-]+)", r"PO\s*No\.?[:\s]*([A-Z0-9\-]+)"]),
    }

def extract_po_data(text):
    return {
        "po_number": extract_pattern(text, [r"PO\s*Number[:\s]*([A-Z0-9\-]+)", r"Purchase\s*Order\s*No\.?[:\s]*([A-Z0-9\-]+)"]),
        "vendor": extract_pattern(text, [r"Vendor[:\s]*(.+?)(?=\s*(?:Date|Amount|$))", r"Supplier[:\s]*(.+?)(?=\s*(?:Date|Amount|$))"]),
        "amount": extract_pattern(text, [r"Amount[:\s₹]*([\d,\.]+)", r"Approved\s*Amount[:\s₹]*([\d,\.]+)", r"Total[:\s₹]*([\d,\.]+)"]),
        "date": extract_pattern(text, [r"Date[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})"])
    }

# ====================== AUDIT RULE #1 ======================
def run_amount_verification(db: Session, invoice: Invoice):
    print(f"\n[AUDIT] Checking Invoice: {invoice.invoice_number} | Amount: {invoice.amount} | PO#: {invoice.po_number} | Vendor: {invoice.vendor}")

    if not invoice.amount:
        print("[AUDIT] No amount found in invoice")
        return None

    po = None
    # Match by PO Number
    if invoice.po_number:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number.ilike(f"%{invoice.po_number}%")).first()

    # Fallback: Match by Vendor
    if not po and invoice.vendor:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.vendor.ilike(f"%{invoice.vendor}%")).first()

    if po and po.amount:
        print(f"[AUDIT] Matched PO: {po.po_number} | PO Amount: {po.amount}")
        if invoice.amount > po.amount:
            difference = invoice.amount - po.amount
            finding = AuditFinding(
                invoice_id=invoice.id,
                po_id=po.id,
                rule_name="Amount Verification",
                risk_level="HIGH",
                description=f"Invoice amount (₹{invoice.amount}) exceeds PO amount (₹{po.amount})",
                difference=difference
            )
            db.add(finding)
            db.commit()
            db.refresh(finding)
            print(f"[AUDIT] ✅ HIGH RISK Finding Created! Difference: ₹{difference}")
            return finding
        else:
            print("[AUDIT] Amount is within PO limit")
    else:
        print("[AUDIT] No matching PO found")

    return None

# ====================== UPLOAD ENDPOINT ======================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            raise HTTPException(400, "Could not extract text from PDF")

        document_type = detect_document_type(text)

        if document_type == "purchase_order":
            data = extract_po_data(text)
            po = PurchaseOrder(
                po_number=data.get("po_number"),
                vendor=data.get("vendor"),
                amount=float(str(data.get("amount", "")).replace(",", "").replace("₹", "")) or None,
                date=data.get("date")
            )
            db.add(po)
            db.commit()
            db.refresh(po)
            audit_result = None
        else:
            data = extract_invoice_data(text)
            invoice = Invoice(
                invoice_number=data.get("invoice_number"),
                vendor=data.get("vendor"),
                amount=float(str(data.get("amount", "")).replace(",", "").replace("₹", "")) or None,
                date=data.get("date"),
                gst_number=data.get("gst_number"),
                po_number=data.get("po_number")
            )
            db.add(invoice)
            db.commit()
            db.refresh(invoice)

            audit_result = run_amount_verification(db, invoice)

        return {
            "filename": file.filename,
            "document_type": document_type,
            "extracted_data": data,
            "audit_finding": {
                "risk_level": audit_result.risk_level,
                "description": audit_result.description,
                "difference": audit_result.difference
            } if audit_result else None,
            "message": "Processed successfully"
        }

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(500, str(e))

# ====================== VIEW DATA ======================
@app.get("/data")
def get_all_data(db: Session = Depends(get_db)):
    return {
        "invoices": db.query(Invoice).all(),
        "purchase_orders": db.query(PurchaseOrder).all(),
        "audit_findings": db.query(AuditFinding).all()
    }