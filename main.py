from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import shutil
import os
import re
import traceback
import uuid
from pathlib import Path

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


# ====================== HELPERS ======================
def safe_float(value):
    if not value:
        return None
    try:
        cleaned = str(value).replace(",", "").replace("₹", "").replace(" ", "").strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def extract_pattern(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def detect_document_type(text: str):
    lower = text.lower()

    # Invoice keywords
    if any(word in lower for word in [
        "tax invoice",
        "invoice number",
        "invoice no",
        "invoice"
    ]):
        return "invoice"

    # Purchase Order keywords
    if any(word in lower for word in [
        "purchase order",
        "purchase order number",
        "purchase order no"
    ]):
        return "purchase_order"

    return "invoice"  # default to invoice


# ====================== IMPROVED EXTRACTION ======================
def extract_invoice_data(text):
    # Special handling for Vendor
    vendor = extract_pattern(text, [
        r"Vendor\s*:?\s*([^\n\r]+)",
        r"Supplier\s*:?\s*([^\n\r]+)",
        r"From\s*:?\s*([^\n\r]+)"
    ])
    if vendor:
        vendor = re.sub(r"\s+", " ", vendor).strip()

    data = {
        "invoice_number": extract_pattern(text, [
            r"Invoice\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Invoice\s*No\.?[:\s]*([A-Z0-9\-]+)",
            r"Bill\s*No\.?[:\s]*([A-Z0-9\-]+)",
            r"Invoice[:\s]*([A-Z0-9\-]+)"
        ]),
        "vendor": vendor,
        "amount": extract_pattern(text, [
            r"Grand\s*Total[:\s₹]*([\d,\.]+)",
            r"Total\s*Amount[:\s₹]*([\d,\.]+)",
            r"Amount[:\s₹]*([\d,\.]+)",
            r"₹\s*([\d,\.]+)"
        ]),
        "date": extract_pattern(text, [r"Date[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})"]),
        "gst_number": extract_pattern(text, [r"GST(?:IN)?[:\s]*([A-Z0-9]+)"]),
        "po_number": extract_pattern(text, [
            r"PO\s*Number[:\s]*([A-Z0-9\-]+)",
            r"PO\s*No\.?[:\s]*([A-Z0-9\-]+)"
        ]),
    }
    print("Extracted Invoice Data:", data)   # Debug
    return data


def extract_po_data(text):
    # Special handling for Vendor
    vendor = extract_pattern(text, [
        r"Vendor\s*:?\s*([^\n\r]+)",
        r"Supplier\s*:?\s*([^\n\r]+)"
    ])
    if vendor:
        vendor = re.sub(r"\s+", " ", vendor).strip()

    data = {
        "po_number": extract_pattern(text, [
            r"PO\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Purchase\s*Order\s*No\.?[:\s]*([A-Z0-9\-]+)",
            r"PO[:\s]*([A-Z0-9\-]+)"
        ]),
        "vendor": vendor,
        "amount": extract_pattern(text, [
            r"Total[:\s₹]*([\d,\.]+)",
            r"Grand\s*Total[:\s₹]*([\d,\.]+)",
            r"Amount[:\s₹]*([\d,\.]+)"
        ]),
        "date": extract_pattern(text, [r"Date[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})"])
    }
    print("Extracted PO Data:", data)
    return data


# ====================== AUDIT RULES ======================
def run_amount_verification(db: Session, invoice: Invoice):
    if not invoice.amount:
        return None

    po = None
    if invoice.po_number:
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number.ilike(f"%{invoice.po_number}%")
        ).first()

    if not po and invoice.vendor:
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.vendor.ilike(f"%{invoice.vendor}%")
        ).first()

    if po and po.amount and invoice.amount > po.amount:
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
        return finding
    return None


def run_missing_field_detection(db: Session, invoice: Invoice):
    findings = []
    required = {
        "Invoice Number": invoice.invoice_number,
        "Vendor Name": invoice.vendor,
        "Amount": invoice.amount,
        "Date": invoice.date,
        "GST Number": invoice.gst_number
    }

    for field, value in required.items():
        if not value or str(value).strip() == "":
            finding = AuditFinding(
                invoice_id=invoice.id,
                rule_name="Missing Information Detection",
                risk_level="MEDIUM",
                description=f"Mandatory field missing: {field}"
            )
            db.add(finding)
            findings.append(finding)

    if findings:
        db.commit()
        for f in findings:
            db.refresh(f)
    return findings


# ====================== UPLOAD ENDPOINT ======================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = None
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Only PDF files are allowed")

        file_ext = Path(file.filename).suffix
        safe_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

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
        data = None
        amount_result = None
        missing_results = []

        if document_type == "purchase_order":
            data = extract_po_data(text)
            po = PurchaseOrder(
                po_number=data.get("po_number"),
                vendor=data.get("vendor"),
                amount=safe_float(data.get("amount")),
                date=data.get("date")
            )
            db.add(po)
            db.commit()
            db.refresh(po)
        else:
            data = extract_invoice_data(text)
            invoice = Invoice(
                invoice_number=data.get("invoice_number"),
                vendor=data.get("vendor"),
                amount=safe_float(data.get("amount")),
                date=data.get("date"),
                gst_number=data.get("gst_number"),
                po_number=data.get("po_number")
            )
            db.add(invoice)
            db.commit()
            db.refresh(invoice)

            amount_result = run_amount_verification(db, invoice)
            missing_results = run_missing_field_detection(db, invoice)

        return {
            "success": True,
            "filename": file.filename,
            "document_type": document_type,
            "extracted_data": data,
            "audit_findings": (
                ([{
                    "risk_level": amount_result.risk_level,
                    "description": amount_result.description,
                    "difference": amount_result.difference
                }] if amount_result else [])
                + [{
                    "risk_level": f.risk_level,
                    "description": f.description,
                    "difference": f.difference
                } for f in missing_results]
            ),
            "message": "Processed successfully"
        }

    except HTTPException:
        raise
    except Exception:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete file {file_path}: {e}")


# ====================== DASHBOARD APIs ======================
@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_docs = db.query(Invoice).count() + db.query(PurchaseOrder).count()
    total_findings = db.query(AuditFinding).count()
    high_risk = db.query(AuditFinding).filter(AuditFinding.risk_level == "HIGH").count()
    medium_risk = db.query(AuditFinding).filter(AuditFinding.risk_level == "MEDIUM").count()

    return {
        "documents_processed": total_docs,
        "total_findings": total_findings,
        "high_risk": high_risk,
        "medium_risk": medium_risk
    }


@app.get("/api/findings")
def get_findings(db: Session = Depends(get_db)):
    findings = db.query(AuditFinding).order_by(AuditFinding.id.desc()).all()
    return [
        {
            "id": f.id,
            "rule_name": f.rule_name,
            "description": f.description,
            "risk_level": f.risk_level,
            "difference": f.difference,
            "created_at": f.created_at.isoformat() if hasattr(f, 'created_at') and f.created_at else None
        }
        for f in findings
    ]


@app.get("/data")
def get_all_data(db: Session = Depends(get_db)):
    return {
        "invoices": [
            {
                "id": i.id,
                "invoice_number": i.invoice_number,
                "vendor": i.vendor,
                "amount": i.amount,
                "date": i.date,
                "gst_number": i.gst_number,
                "po_number": i.po_number
            }
            for i in db.query(Invoice).all()
        ],
        "purchase_orders": [
            {
                "id": p.id,
                "po_number": p.po_number,
                "vendor": p.vendor,
                "amount": p.amount,
                "date": p.date
            }
            for p in db.query(PurchaseOrder).all()
        ],
        "audit_findings": [
            {
                "id": f.id,
                "invoice_id": f.invoice_id,
                "po_id": f.po_id,
                "rule_name": f.rule_name,
                "risk_level": f.risk_level,
                "description": f.description,
                "difference": f.difference,
                "created_at": f.created_at.isoformat() if hasattr(f, 'created_at') and f.created_at else None
            }
            for f in db.query(AuditFinding).all()
        ]
    }