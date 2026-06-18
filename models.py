from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, index=True)
    vendor = Column(String)
    amount = Column(Float)
    date = Column(String)
    gst_number = Column(String, nullable=True)
    po_number = Column(String, nullable=True)
    tax = Column(Float, nullable=True)

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, index=True)
    vendor = Column(String)
    amount = Column(Float)
    date = Column(String)

class AuditFinding(Base):
    __tablename__ = "audit_findings"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    rule_name = Column(String)
    risk_level = Column(String)          # HIGH, MEDIUM, LOW
    description = Column(String)
    difference = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())