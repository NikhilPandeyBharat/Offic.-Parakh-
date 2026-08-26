import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Table
)
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # CAPTURE_OPERATOR, VERIFICATION_OFFICER, SENIOR_ENFORCEMENT_OFFICER, ADMIN
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    audit_logs = relationship("AuditLog", back_populates="user")
    inspections = relationship("Inspection", back_populates="officer")

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, unique=True, index=True)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    risk_score = Column(Float, default=0.0)
    last_inspection_date = Column(DateTime)
    compliance_rate = Column(Float, default=100.0)  # Percentage

    products = relationship("Product", back_populates="manufacturer")
    corrective_actions = relationship("CorrectiveAction", back_populates="manufacturer")

class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    base_risk_weight = Column(Float, default=10.0)

    products = relationship("Product", back_populates="category")
    rules = relationship("LegalRule", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    barcode = Column(String, unique=True, index=True, nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    current_version = Column(String, default="v1")
    status = Column(String, default="ACTIVE")  # ACTIVE, FLAGGED, UNDER_INVESTIGATION
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("ProductCategory", back_populates="products")
    versions = relationship("ProductVersion", back_populates="product")
    lots = relationship("Lot", back_populates="product")

class ProductVersion(Base):
    __tablename__ = "product_versions"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    version_number = Column(String, nullable=False)  # v1, v2, etc.
    packaging_hash = Column(String)  # Deterministic representation for similarity comparison
    image_url_front = Column(String)
    image_url_back = Column(String)
    image_url_left = Column(String)
    image_url_right = Column(String)
    image_url_top = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="versions")

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String, unique=True, index=True, nullable=False)
    date_received = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, INSPECTED, IN_PROGRESS
    lot_count = Column(Integer, default=0)
    item_count = Column(Integer, default=0)

    lots = relationship("Lot", back_populates="shipment")

class Lot(Base):
    __tablename__ = "lots"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    risk_score = Column(Float, default=0.0)
    priority_status = Column(String, default="NORMAL")  # CRITICAL, HIGH, MEDIUM, LOW

    shipment = relationship("Shipment", back_populates="lots")
    product = relationship("Product", back_populates="lots")
    samples = relationship("Sample", back_populates="lot")

class Sample(Base):
    __tablename__ = "samples"
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    serial_number = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, CAPTURED, EVALUATED, COMPLIANT, VIOLATION, REVIEW

    lot = relationship("Lot", back_populates="samples")
    inspections = relationship("Inspection", back_populates="sample")

class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, REVIEW, REJECTED
    overall_coverage = Column(Float, default=0.0)  # Percentage of declarations evaluated
    overall_compliance = Column(String, default="PENDING")  # COMPLIANT, NON_COMPLIANT, REQUIRES_VERIFICATION
    final_decision = Column(String)  # PASS, FAIL, RE-INSPECT, PROSECUTE
    notes = Column(Text)

    sample = relationship("Sample", back_populates="inspections")
    officer = relationship("User", back_populates="inspections")
    captured_images = relationship("CapturedImage", back_populates="inspection")
    extracted_facts = relationship("ExtractedFact", back_populates="inspection")
    compliance_evaluations = relationship("ComplianceEvaluation", back_populates="inspection")
    violations = relationship("Violation", back_populates="inspection")
    evidence = relationship("Evidence", back_populates="inspection")
    corrective_actions = relationship("CorrectiveAction", back_populates="inspection")

class CapturedImage(Base):
    __tablename__ = "captured_images"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    camera_view = Column(String, nullable=False)  # FRONT, BACK, LEFT, RIGHT, TOP
    image_path = Column(String, nullable=False)
    quality_status = Column(String, default="GOOD")  # GOOD, BLUR, GLARE, OCCLUDED, INSUFFICIENT_COVERAGE
    captured_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspection = relationship("Inspection", back_populates="captured_images")
    ocr_results = relationship("OCRResult", back_populates="captured_image")

class OCRResult(Base):
    __tablename__ = "ocr_results"
    id = Column(Integer, primary_key=True, index=True)
    captured_image_id = Column(Integer, ForeignKey("captured_images.id"), nullable=False)
    field_name = Column(String)  # Suggested field (e.g. MRP, Net Qty)
    raw_text = Column(Text, nullable=False)
    confidence = Column(Float, default=100.0)
    bounding_box = Column(String)  # JSON formatted "x,y,w,h" coordinates

    captured_image = relationship("CapturedImage", back_populates="ocr_results")

class ExtractedFact(Base):
    __tablename__ = "extracted_facts"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    field_name = Column(String, nullable=False)  # mrp, net_qty, manufacturer_name, packed_date, consumer_care_phone, consumer_care_email, etc.
    extracted_value = Column(String)
    normalized_value = Column(String)  # normalized (e.g., Rs. 249 -> 249 INR)
    confidence = Column(Float, default=100.0)
    source_image_id = Column(Integer, ForeignKey("captured_images.id"))

    inspection = relationship("Inspection", back_populates="extracted_facts")

class LegalRule(Base):
    __tablename__ = "legal_rules"
    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String, unique=True, index=True, nullable=False)  # e.g., RULE-DEMO-001
    title = Column(String, nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    severity = Column(String, default="MEDIUM")  # CRITICAL, MAJOR, MINOR

    category = relationship("ProductCategory", back_populates="rules")
    versions = relationship("RuleVersion", back_populates="rule")

class RuleVersion(Base):
    __tablename__ = "rule_versions"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("legal_rules.id"), nullable=False)
    version = Column(Integer, default=1)
    effective_date = Column(DateTime, default=datetime.datetime.utcnow)
    validation_criteria = Column(Text)  # Rule description check pattern
    is_active = Column(Boolean, default=True)

    rule = relationship("LegalRule", back_populates="versions")
    compliance_evaluations = relationship("ComplianceEvaluation", back_populates="rule_version")
    violations = relationship("Violation", back_populates="rule_version")

class ComplianceEvaluation(Base):
    __tablename__ = "compliance_evaluations"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id"), nullable=False)
    status = Column(String, default="PENDING")  # COMPLIANT, NON_COMPLIANT, REQUIRES_VERIFICATION
    notes = Column(Text)

    inspection = relationship("Inspection", back_populates="compliance_evaluations")
    rule_version = relationship("RuleVersion", back_populates="compliance_evaluations")

class Violation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id"), nullable=False)
    fact_id = Column(Integer, ForeignKey("extracted_facts.id"))
    severity = Column(String, default="MEDIUM")
    description = Column(Text)

    inspection = relationship("Inspection", back_populates="violations")
    rule_version = relationship("RuleVersion", back_populates="violations")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    type = Column(String, nullable=False)  # IMAGE, TEXT
    file_path = Column(String)  # Image path
    bounding_box = Column(String)  # Crop coordinates "x,y,w,h"
    confidence = Column(Float, default=100.0)
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id"))

    inspection = relationship("Inspection", back_populates="evidence")

class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    date_issued = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime)
    status = Column(String, default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED, FAILED, OVERDUE
    notes = Column(Text)

    inspection = relationship("Inspection", back_populates="corrective_actions")
    manufacturer = relationship("Manufacturer", back_populates="corrective_actions")
    reinspections = relationship("Reinspection", back_populates="corrective_action")

class Reinspection(Base):
    __tablename__ = "reinspections"
    id = Column(Integer, primary_key=True, index=True)
    original_inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    corrective_action_id = Column(Integer, ForeignKey("corrective_actions.id"), nullable=False)
    new_inspection_id = Column(Integer, ForeignKey("inspections.id"))  # Linked after re-inspection is completed
    status = Column(String, default="SCHEDULED")  # SCHEDULED, COMPLETED, OVERDUE
    comparison_result = Column(String)  # RESOLVED, REPEATED_VIOLATION, NEW_VIOLATIONS

    corrective_action = relationship("CorrectiveAction", back_populates="reinspections")

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String, nullable=False)  # MANUFACTURER, PRODUCT, LOT
    target_id = Column(Integer, nullable=False)
    score = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    factors = relationship("RiskFactor", back_populates="risk_score")

class RiskFactor(Base):
    __tablename__ = "risk_factors"
    id = Column(Integer, primary_key=True, index=True)
    risk_score_id = Column(Integer, ForeignKey("risk_scores.id"), nullable=False)
    factor_name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    value = Column(Float, nullable=False)

    risk_score = relationship("RiskScore", back_populates="factors")

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String, nullable=False)  # MANUFACTURER, PRODUCT, LOT
    target_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # PRIORITY_SAMPLE, ENHANCED_INSPECTION, ROUTINE_MONITORING, PROSECUTE
    priority = Column(String, default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # LOGIN, CAPTURE, OCR_CORRECTION, VERIFICATION, RULE_MODIFICATION, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(Text)

    user = relationship("User", back_populates="audit_logs")

class InvestigationCase(Base):
    __tablename__ = "investigation_cases"
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True, nullable=False)  # e.g., CASE-2026-0001
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    status = Column(String, default="OPEN")  # OPEN, UNDER_REVIEW, INVESTIGATION, RESOLVED, CLOSED
    risk_level = Column(String, default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
