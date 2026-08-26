import os
import datetime
import random
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import engine, get_db, Base
from backend.models import (
    User, Manufacturer, ProductCategory, Product, ProductVersion, Shipment, Lot, Sample,
    Inspection, CapturedImage, OCRResult, ExtractedFact, LegalRule, RuleVersion,
    ComplianceEvaluation, Violation, Evidence, CorrectiveAction, Reinspection,
    RiskScore, RiskFactor, Recommendation, AuditLog, InvestigationCase
)
from backend.auth import (
    verify_password, get_password_hash, create_access_token, get_current_user, RoleChecker
)
from backend.schemas import (
    UserLogin, Token, UserResponse, ShipmentResponse, ShipmentDetailResponse,
    LotResponse, SampleResponse, InspectionResponse, CapturedImageResponse,
    ExtractedFactResponse, ComplianceEvaluationResponse, ViolationResponse,
    EvidenceResponse, CorrectiveActionResponse, ReinspectionResponse,
    RiskScoreResponse, RecommendationResponse, InvestigationCaseResponse,
    AuditLogResponse, LegalRuleResponse, RuleCreateRequest, CorrectiveActionCreateRequest,
    CorrectiveActionUpdateRequest, ReinspectionScheduleRequest, CaseCreateRequest,
    CaseUpdateRequest, FactEditRequest, InspectionDecisionRequest, Token as TokenSchema,
    ManufacturerResponse, ProductResponse
)
from backend.engine import ExplainableRiskEngine, LegalComplianceEngine
from backend.providers import SimulatedCameraProvider, DemoOCRProvider, DemoProductIdentificationProvider
from backend.report import generate_inspection_report

# Initialize database tables if not already created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PARAKH API", description="AI-Assisted Legal Metrology Inspection Intelligence Platform")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prototype, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
os.makedirs("backend/static/reports", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Providers init
camera_provider = SimulatedCameraProvider()
ocr_provider = DemoOCRProvider()
id_provider = DemoProductIdentificationProvider()

# --- AUTHENTICATION ---
@app.post("/api/auth/login", response_model=TokenSchema)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    
    # Audit log login
    db.add(AuditLog(user_id=user.id, action="LOGIN", details=f"User {user.username} logged in with role {user.role}."))
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name or user.username
    }

# --- DASHBOARD & ANALYTICS ---
@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_shipments = db.query(Shipment).count()
    inspected_shipments = db.query(Shipment).filter(Shipment.status == "INSPECTED").count()
    
    total_insps = db.query(Inspection).filter(Inspection.status == "COMPLETED").count()
    compliant_insps = db.query(Inspection).filter(
        Inspection.status == "COMPLETED",
        Inspection.overall_compliance == "COMPLIANT"
    ).count()
    
    compliance_rate = (compliant_insps / total_insps * 100) if total_insps > 0 else 100.0

    total_manufacturers = db.query(Manufacturer).count()
    high_risk_mfg = db.query(Manufacturer).filter(Manufacturer.risk_score >= 60.0).count()
    
    violations_count = db.query(Violation).count()
    open_corrective = db.query(CorrectiveAction).filter(CorrectiveAction.status == "OPEN").count()
    pending_reinspection = db.query(Reinspection).filter(Reinspection.status == "SCHEDULED").count()
    
    return {
        "shipments_count": total_shipments,
        "inspected_shipments_count": inspected_shipments,
        "inspections_count": total_insps,
        "compliance_rate": round(compliance_rate, 1),
        "manufacturers_count": total_manufacturers,
        "high_risk_manufacturers_count": high_risk_mfg,
        "violations_count": violations_count,
        "open_corrective_actions_count": open_corrective,
        "pending_reinspections_count": pending_reinspection
    }

@app.get("/api/dashboard/trends")
def get_dashboard_trends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Group past inspections by date (mock trend)
    # Return last 6 months compliance trend
    today = datetime.datetime.utcnow()
    trends = []
    for i in range(5, -1, -1):
        month_start = today - datetime.timedelta(days=30 * i)
        month_str = month_start.strftime("%b %Y")
        
        # Calculate rates for that mock period
        # We can randomize/simulate based on DB seeding
        insps = db.query(Inspection).filter(
            Inspection.status == "COMPLETED",
            Inspection.timestamp <= month_start + datetime.timedelta(days=15),
            Inspection.timestamp >= month_start - datetime.timedelta(days=15)
        ).all()
        
        count = len(insps)
        fails = len([x for x in insps if x.overall_compliance == "NON_COMPLIANT"])
        rate = ((count - fails) / count * 100) if count > 0 else 85.0
        
        trends.append({
            "period": month_str,
            "inspections": max(count, random.randint(10, 30)) if i > 0 else count,
            "violations": max(fails, random.randint(2, 8)) if i > 0 else fails,
            "compliance_rate": round(rate, 1)
        })
    return trends

@app.get("/api/dashboard/category-analytics")
def get_category_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    categories = db.query(ProductCategory).all()
    results = []
    for cat in categories:
        prods = db.query(Product).filter(Product.category_id == cat.id).all()
        prod_ids = [p.id for p in prods]
        
        insps_count = db.query(Inspection).join(Sample).join(Lot).filter(Lot.product_id.in_(prod_ids)).count() if prod_ids else 0
        viols_count = db.query(Violation).join(Inspection).join(Sample).join(Lot).filter(Lot.product_id.in_(prod_ids)).count() if prod_ids else 0
        
        compliance_rate = 100.0
        if insps_count > 0:
            fails = db.query(Inspection).join(Sample).join(Lot).filter(
                Lot.product_id.in_(prod_ids),
                Inspection.overall_compliance == "NON_COMPLIANT"
            ).count()
            compliance_rate = ((insps_count - fails) / insps_count) * 100
            
        results.append({
            "category": cat.name,
            "inspections": insps_count,
            "violations": viols_count,
            "compliance_rate": round(compliance_rate, 1),
            "risk": "HIGH" if compliance_rate < 75.0 else "MEDIUM" if compliance_rate < 90.0 else "LOW"
        })
    return results

@app.get("/api/dashboard/geography-analytics")
def get_geography_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Returns violation count grouped by states
    mfg_states = db.query(Manufacturer.state, func.count(Violation.id).label("violation_count")).join(
        Product, Product.manufacturer_id == Manufacturer.id
    ).join(
        Lot, Lot.product_id == Product.id
    ).join(
        Sample, Sample.lot_id == Lot.id
    ).join(
        Inspection, Inspection.sample_id == Sample.id
    ).join(
        Violation, Violation.inspection_id == Inspection.id
    ).group_by(Manufacturer.state).all()

    return [{"state": state or "Other", "violations": count} for state, count in mfg_states]

# --- SHIPMENTS & LOTS ---
@app.get("/api/shipments", response_model=List[ShipmentResponse])
def list_shipments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Shipment).order_by(Shipment.date_received.desc()).all()

@app.get("/api/shipments/{id}", response_model=ShipmentDetailResponse)
def get_shipment_details(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shp = db.query(Shipment).filter(Shipment.id == id).first()
    if not shp:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shp

@app.post("/api/shipments/{id}/prioritize")
def run_shipment_prioritization(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Recalculates risk ratings dynamically for all product lots inside this shipment
    based on the latest manufacturer history and category rules.
    """
    shp = db.query(Shipment).filter(Shipment.id == id).first()
    if not shp:
        raise HTTPException(status_code=404, detail="Shipment not found")
        
    for lot in shp.lots:
        prod = lot.product
        mfg = prod.manufacturer
        
        # Calculate manufacturer latest risk
        risk_calc = ExplainableRiskEngine.calculate_manufacturer_risk(db, mfg.id)
        
        # Recalculate lot risk factor: base category risk + manufacturer risk weight
        base_cat_risk = prod.category.base_risk_weight
        new_lot_risk = base_cat_risk + (risk_calc["score"] * 0.7)
        new_lot_risk = min(100.0, max(0.0, new_lot_risk))
        
        lot.risk_score = new_lot_risk
        
        # Set priority status
        if new_lot_risk >= 80: lot.priority_status = "CRITICAL"
        elif new_lot_risk >= 60: lot.priority_status = "HIGH"
        elif new_lot_risk >= 40: lot.priority_status = "MEDIUM"
        else: lot.priority_status = "LOW"
        
    db.commit()
    
    # Audit log
    db.add(AuditLog(user_id=current_user.id, action="RISK_RECALCULATION", details=f"Recalculated priority scoring for Shipment ID {shp.shipment_number}."))
    db.commit()

    return {"message": "Dynamic risk prioritization completed successfully."}

# --- SAMPLES ---
@app.get("/api/samples", response_model=List[SampleResponse])
def list_samples(lot_id: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Sample)
    if lot_id:
        query = query.filter(Sample.lot_id == lot_id)
    return query.all()

@app.get("/api/samples/{id}", response_model=SampleResponse)
def get_sample(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    smp = db.query(Sample).filter(Sample.id == id).first()
    if not smp:
        raise HTTPException(status_code=404, detail="Sample not found")
    return smp

# --- INSPECTION OPERATIONS ---
@app.post("/api/inspections/start", response_model=InspectionResponse)
def start_inspection(sample_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Initializes a new Inspection command workflow for a designated sample lot.
    """
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
        
    # Check if there is already an in-progress inspection
    existing = db.query(Inspection).filter(
        Inspection.sample_id == sample_id,
        Inspection.status == "IN_PROGRESS"
    ).first()
    if existing:
        return existing
        
    # Start inspection
    insp = Inspection(
        sample_id=sample_id,
        officer_id=current_user.id,
        status="IN_PROGRESS",
        overall_compliance="PENDING"
    )
    db.add(insp)
    sample.status = "CAPTURED"
    
    # Audit
    db.add(AuditLog(user_id=current_user.id, action="CAPTURE", details=f"Initiated inspection sequence for sample {sample.serial_number}."))
    db.commit()
    db.refresh(insp)
    return insp

@app.post("/api/inspections/{id}/capture")
def run_inspection_capture(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Simulates capturing the product packaging in 3D multi-camera station.
    Returns 5 camera view frames and quality status tags.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    barcode = insp.sample.lot.product.barcode
    
    # Delete existing images if recapturing
    db.query(CapturedImage).filter(CapturedImage.inspection_id == id).delete()
    
    views = camera_provider.capture_views(barcode, session_id=str(id))
    captured_records = []
    
    for view in views:
        img = CapturedImage(
            inspection_id=id,
            camera_view=view["camera_view"],
            image_path=view["image_path"],
            quality_status=view["quality_status"]
        )
        db.add(img)
        db.flush()
        captured_records.append(img)
        
    db.commit()
    return captured_records

@app.post("/api/inspections/{id}/recapture")
def run_camera_recapture(id: int, camera_view: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Recaptures a single failed view angle (operator override).
    Forces quality status to GOOD.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    # Find matching image
    img = db.query(CapturedImage).filter(
        CapturedImage.inspection_id == id,
        CapturedImage.camera_view == camera_view
    ).first()
    
    if not img:
        raise HTTPException(status_code=404, detail="Captured view record not found")
        
    img.quality_status = "GOOD"
    db.add(AuditLog(user_id=current_user.id, action="RECAPTURE", details=f"Operator manually requested recapture for camera view {camera_view}."))
    db.commit()
    db.refresh(img)
    return img

@app.post("/api/inspections/{id}/identify")
def identify_product(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    prod = insp.sample.lot.product
    ident = id_provider.identify_product(prod.barcode)
    
    return {
        "product_id": prod.id,
        "name": prod.name,
        "barcode": prod.barcode,
        "current_version": prod.current_version,
        "manufacturer": prod.manufacturer.name,
        "category": prod.category.name,
        "identification": ident
    }

@app.post("/api/inspections/{id}/ocr")
def run_packaging_ocr(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Runs deterministic OCR extraction from multi-view frames, choosing high-confidence sources.
    Fuses extracted text results into normalized statutory metrology facts.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    barcode = insp.sample.lot.product.barcode
    captured_images = db.query(CapturedImage).filter(CapturedImage.inspection_id == id).all()
    
    # Delete old OCR results & facts
    db.query(ExtractedFact).filter(ExtractedFact.inspection_id == id).delete()
    for img in captured_images:
        db.query(OCRResult).filter(OCRResult.captured_image_id == img.id).delete()
        
    # Extract details view by view
    extracted_fields = {}
    for img in captured_images:
        ocr_boxes = ocr_provider.extract_text(barcode, img.camera_view)
        
        for box in ocr_boxes:
            field = box["field"]
            # Save raw OCR
            res = OCRResult(
                captured_image_id=img.id,
                field_name=field,
                raw_text=box["text"],
                confidence=box["confidence"],
                bounding_box=box["box"]
            )
            db.add(res)
            
            # Evidence Fusion logic: Choose highest confidence OCR reading for each field
            if field != "brand_logo" and field != "logo":
                if field not in extracted_fields or box["confidence"] > extracted_fields[field]["confidence"]:
                    extracted_fields[field] = {
                        "raw_text": box["text"],
                        "confidence": box["confidence"],
                        "image_id": img.id
                    }
                    
    # Facts Normalization & Write
    for field_name, item in extracted_fields.items():
        raw = item["raw_text"]
        norm = "None"
        
        # Simple parsing rules
        if field_name == "mrp":
            # Extract numbers like 150.00 or 249
            digits = "".join(c for c in raw if c.isdigit() or c == '.')
            if digits:
                norm = f"{float(digits):.0f} INR"
        elif field_name == "net_qty":
            # Extract quantity (e.g. 500g or 200ml)
            clean = raw.replace("NET", "").replace("QTY", "").replace("Net", "").replace("Vol", "").replace(":", "").strip()
            norm = clean
        elif field_name == "manufacturer_name":
            # Strip prefixes like "Mfg by:"
            clean = raw.replace("Mfg by:", "").replace("Mfd by", "").replace("Mfg By:", "").strip()
            norm = clean
        elif field_name == "packed_date":
            # Convert 05/2026 -> 2026-05-01
            clean = raw.replace("Pkd:", "").replace("Packed:", "").replace("Packed Date:", "").strip()
            norm = clean # Keep as string for prototype simplicity
        elif field_name == "consumer_care_phone":
            # Extract phone/helpline
            clean = raw.replace("Consumer care cell:", "").replace("Helpline:", "").replace("For feedback write to", "").strip()
            norm = clean
            
        fact = ExtractedFact(
            inspection_id=id,
            field_name=field_name,
            extracted_value=raw,
            normalized_value=norm,
            confidence=item["confidence"],
            source_image_id=item["image_id"]
        )
        db.add(fact)
        
    db.commit()
    
    # Return saved facts
    return db.query(ExtractedFact).filter(ExtractedFact.inspection_id == id).all()

@app.post("/api/inspections/{id}/evaluate")
def run_compliance_evaluation(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Compares observed facts (A) vs legal requirements (B).
    Generates violation reports.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    # Clear old evaluations & violations
    db.query(ComplianceEvaluation).filter(ComplianceEvaluation.inspection_id == id).delete()
    db.query(Violation).filter(Violation.inspection_id == id).delete()
    db.query(Evidence).filter(Evidence.inspection_id == id).delete()
    
    # Run engine evaluation
    result = LegalComplianceEngine.evaluate_compliance(db, id)
    
    # Save compliance evaluations and violations
    for item in result["rules_matrix"]:
        ev_rec = ComplianceEvaluation(
            inspection_id=id,
            rule_version_id=item["rule_version_id"],
            status=item["status"],
            notes=item["notes"]
        )
        db.add(ev_rec)
        db.flush()
        
        if item["status"] == "NON_COMPLIANT":
            # Find fact_id if matched
            matched_fact = db.query(ExtractedFact).filter(
                ExtractedFact.inspection_id == id,
                # Simple field code linking
                ExtractedFact.field_name == ("mrp" if "RULE-DEMO-001" in item["rule_code"] else 
                                             "net_qty" if "RULE-DEMO-002" in item["rule_code"] else
                                             "manufacturer_name" if "RULE-DEMO-003" in item["rule_code"] else
                                             "consumer_care_phone" if "RULE-DEMO-004" in item["rule_code"] else
                                             "packed_date" if "RULE-DEMO-005" in item["rule_code"] else
                                             "country_of_origin")
            ).first()
            
            viol = Violation(
                inspection_id=id,
                rule_version_id=item["rule_version_id"],
                fact_id=matched_fact.id if matched_fact else None,
                severity=item["severity"],
                description=item["notes"]
            )
            db.add(viol)
            db.flush()
            
            # Save Evidence
            source_img_id = matched_fact.source_image_id if matched_fact else None
            img_rec = db.query(CapturedImage).filter(CapturedImage.id == source_img_id).first() if source_img_id else None
            
            evidence = Evidence(
                inspection_id=id,
                type="IMAGE",
                file_path=img_rec.image_path if img_rec else "/static/images/demo/placeholder.jpg",
                bounding_box="100,200,300,80", # mock bbox coordinates
                confidence=item["confidence"],
                rule_version_id=item["rule_version_id"]
            )
            db.add(evidence)
            
    insp.overall_coverage = result["overall_coverage"]
    insp.overall_compliance = result["overall_compliance"]
    
    db.commit()
    return result

@app.post("/api/inspections/{id}/edit-fact")
def edit_extracted_fact(id: int, edit_req: FactEditRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Verification Officer correction override.
    Edits a label reading and triggers compliance re-evaluation.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    fact = db.query(ExtractedFact).filter(
        ExtractedFact.inspection_id == id,
        ExtractedFact.field_name == edit_req.field_name
    ).first()
    
    if not fact:
        raise HTTPException(status_code=404, detail="Fact field not found")
        
    old_val = fact.extracted_value
    fact.extracted_value = edit_req.edited_value
    
    # Recalculate normalized value
    digits = "".join(c for c in edit_req.edited_value if c.isdigit() or c == '.')
    if edit_req.field_name == "mrp" and digits:
        fact.normalized_value = f"{float(digits):.0f} INR"
    else:
        fact.normalized_value = edit_req.edited_value
        
    fact.confidence = 100.0  # Manually corrected confidence
    
    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="OCR_CORRECTION",
        details=f"Corrected field '{edit_req.field_name}' on Inspection {id} from '{old_val}' to '{edit_req.edited_value}'."
    ))
    db.commit()
    
    # Trigger auto-re-evaluation
    run_compliance_evaluation(id, db, current_user)
    
    return db.query(ExtractedFact).filter(ExtractedFact.inspection_id == id).all()

@app.post("/api/inspections/{id}/decision", response_model=InspectionResponse)
def submit_inspection_decision(id: int, decision_req: InspectionDecisionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Submits the final human inspector decision (PASS / FAIL / PROSECUTE).
    Updates database historical metrics and triggers corrective actions.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    insp.status = "COMPLETED"
    insp.final_decision = decision_req.final_decision
    insp.notes = decision_req.notes
    
    sample = insp.sample
    
    # Update sample status
    if decision_req.final_decision == "PASS":
        sample.status = "COMPLIANT"
    elif decision_req.final_decision == "FAIL" or decision_req.final_decision == "PROSECUTE":
        sample.status = "VIOLATION"
    else:
        sample.status = "REVIEW"
        
    # Auto-generate Corrective Action if FAIL or PROSECUTE and not yet created
    if decision_req.final_decision in ["FAIL", "PROSECUTE"]:
        existing_action = db.query(CorrectiveAction).filter(CorrectiveAction.inspection_id == id).first()
        if not existing_action:
            due_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            action = CorrectiveAction(
                inspection_id=id,
                manufacturer_id=sample.lot.product.manufacturer_id,
                product_id=sample.lot.product_id,
                date_issued=datetime.datetime.utcnow(),
                due_date=due_date,
                status="OPEN",
                notes=f"Auto-generated action from Inspection ID INSP-{id:06d}. Fail reason: {decision_req.notes}"
            )
            db.add(action)
            db.flush()
            
            # Recalculate Manufacturer Risk immediately since violation is verified
            mfg = sample.lot.product.manufacturer
            risk_calc = ExplainableRiskEngine.calculate_manufacturer_risk(db, mfg.id)
            mfg.risk_score = risk_calc["score"]
            mfg.last_inspection_date = datetime.datetime.utcnow()
            
    db.add(AuditLog(
        user_id=current_user.id,
        action="VERIFICATION",
        details=f"Inspection ID INSP-{id:06d} finalized. Verdict: {decision_req.final_decision}."
    ))
    db.commit()
    db.refresh(insp)
    return insp

@app.get("/api/inspections/{id}", response_model=InspectionResponse)
def get_inspection(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return insp

@app.get("/api/inspections/{id}/pdf")
def download_inspection_pdf(id: int, db: Session = Depends(get_db)):
    """
    Generates and returns the downloadable PDF report.
    """
    pdf_filename = f"inspection_report_{id}.pdf"
    filepath = f"backend/static/reports/{pdf_filename}"
    
    # Re-generate PDF report
    generate_inspection_report(db, id, filepath)
    
    # Audit log (if auth can be verified, otherwise skip log)
    return FileResponse(
        path=filepath,
        filename=pdf_filename,
        media_type="application/pdf"
    )

# --- MANUFACTURERS ---
@app.get("/api/manufacturers", response_model=List[ManufacturerResponse])
def list_manufacturers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Manufacturer).order_by(Manufacturer.risk_score.desc()).all()

@app.get("/api/manufacturers/{id}")
def get_manufacturer_profile(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mfg = db.query(Manufacturer).filter(Manufacturer.id == id).first()
    if not mfg:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
        
    # Get products compliance history
    mfg_products = db.query(Product).filter(Product.manufacturer_id == id).all()
    prod_ids = [p.id for p in mfg_products]
    
    inspections = []
    if prod_ids:
        inspections = db.query(Inspection).join(Sample).join(Lot).filter(Lot.product_id.in_(prod_ids)).order_by(Inspection.timestamp.desc()).all()
        
    # Risk breakdown
    risk_info = ExplainableRiskEngine.calculate_manufacturer_risk(db, id)
    
    # Corrective actions
    actions = db.query(CorrectiveAction).filter(CorrectiveAction.manufacturer_id == id).all()
    
    return {
        "manufacturer": mfg,
        "products_count": len(mfg_products),
        "inspections_count": len(inspections),
        "risk_explanation": risk_info,
        "recent_inspections": [
            {
                "id": insp.id,
                "product_name": insp.sample.lot.product.name,
                "timestamp": insp.timestamp,
                "compliance": insp.overall_compliance,
                "decision": insp.final_decision
            } for insp in inspections[:10]
        ],
        "corrective_actions": actions
    }

# --- PRODUCTS ---
@app.get("/api/products", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Product).all()

@app.get("/api/products/{id}")
def get_product_details(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prod = db.query(Product).filter(Product.id == id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    versions = db.query(ProductVersion).filter(ProductVersion.product_id == id).order_by(ProductVersion.created_at.desc()).all()
    
    insps = db.query(Inspection).join(Sample).join(Lot).filter(
        Lot.product_id == id
    ).order_by(Inspection.timestamp.desc()).all()
    
    history_timeline = []
    for insp in insps:
        history_timeline.append({
            "date": insp.timestamp,
            "status": insp.overall_compliance,
            "decision": insp.final_decision,
            "inspection_id": insp.id
        })
        
    return {
        "product": prod,
        "versions": versions,
        "timeline": history_timeline
    }

# --- CORRECTIVE ACTIONS ---
@app.get("/api/corrective-actions", response_model=List[CorrectiveActionResponse])
def list_corrective_actions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CorrectiveAction).all()

@app.post("/api/corrective-actions", response_model=CorrectiveActionResponse)
def create_corrective_action(req: CorrectiveActionCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    insp = db.query(Inspection).filter(Inspection.id == req.inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    prod = insp.sample.lot.product
    
    action = CorrectiveAction(
        inspection_id=req.inspection_id,
        manufacturer_id=prod.manufacturer_id,
        product_id=prod.id,
        date_issued=datetime.datetime.utcnow(),
        due_date=datetime.datetime.utcnow() + datetime.timedelta(days=req.due_days),
        status="OPEN",
        notes=req.notes or f"Notice issued regarding metrology label failure."
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action

@app.put("/api/corrective-actions/{id}", response_model=CorrectiveActionResponse)
def update_corrective_action(id: int, req: CorrectiveActionUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    action = db.query(CorrectiveAction).filter(CorrectiveAction.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    action.status = req.status
    if req.notes:
        action.notes = req.notes
        
    # Recalculate Manufacturer risk if corrective action status is updated
    mfg = action.manufacturer
    risk_calc = ExplainableRiskEngine.calculate_manufacturer_risk(db, mfg.id)
    mfg.risk_score = risk_calc["score"]
    
    db.add(AuditLog(
        user_id=current_user.id,
        action="CORRECTIVE_ACTION_UPDATE",
        details=f"Updated corrective action {id} status to {req.status}."
    ))
    db.commit()
    db.refresh(action)
    return action

# --- RE-INSPECTIONS ---
@app.get("/api/reinspections", response_model=List[ReinspectionResponse])
def list_reinspections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Reinspection).all()

@app.post("/api/reinspections/schedule", response_model=ReinspectionResponse)
def schedule_reinspection(req: ReinspectionScheduleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    action = db.query(CorrectiveAction).filter(CorrectiveAction.id == req.corrective_action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
        
    # Create reinspection scheduling link
    re_insp = Reinspection(
        original_inspection_id=action.inspection_id,
        corrective_action_id=action.id,
        status="SCHEDULED"
    )
    db.add(re_insp)
    
    # Mark target lot sample status as pending recapture
    new_sample = Sample(
        lot_id=action.inspection.sample.lot_id,
        serial_number=f"RE-{action.inspection.sample.serial_number}",
        status="PENDING"
    )
    db.add(new_sample)
    
    db.add(AuditLog(
        user_id=current_user.id,
        action="REINSPECTION_SCHEDULE",
        details=f"Scheduled re-inspection target sample for product {action.product.name}."
    ))
    db.commit()
    db.refresh(re_insp)
    return re_insp

# --- CASES / ENFORCEMENT ---
@app.get("/api/cases", response_model=List[InvestigationCaseResponse])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(InvestigationCase).all()

@app.post("/api/cases", response_model=InvestigationCaseResponse)
def create_case(req: CaseCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mfg = db.query(Manufacturer).filter(Manufacturer.id == req.manufacturer_id).first()
    if not mfg:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
        
    count = db.query(InvestigationCase).count()
    case = InvestigationCase(
        case_number=f"CASE-2026-{count+1:04d}",
        manufacturer_id=req.manufacturer_id,
        product_id=req.product_id,
        shipment_id=req.shipment_id,
        status="OPEN",
        risk_level=req.risk_level,
        notes=req.notes
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

@app.put("/api/cases/{id}", response_model=InvestigationCaseResponse)
def update_case(id: int, req: CaseUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = req.status
    if req.notes:
        case.notes = req.notes
    db.commit()
    db.refresh(case)
    return case

# --- RULES & AUDIT ---
@app.get("/api/rules", response_model=List[LegalRuleResponse])
def list_rules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(LegalRule).all()

@app.post("/api/rules", response_model=LegalRuleResponse)
def create_new_rule(req: RuleCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = LegalRule(
        rule_code=req.rule_code,
        title=req.title,
        description=f"DEMO RULE - {req.description}",
        severity=req.severity,
        category_id=req.category_id
    )
    db.add(rule)
    db.flush()
    rv = RuleVersion(rule_id=rule.id, version=1, is_active=True)
    db.add(rv)
    
    db.add(AuditLog(
        user_id=current_user.id,
        action="RULE_MODIFICATION",
        details=f"Created new legal rule provision: {req.rule_code}."
    ))
    db.commit()
    db.refresh(rule)
    return rule

@app.get("/api/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()

# --- ADMIN USER MANAGEMENT ---
@app.get("/api/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify Admin role
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized user administrative access level")
    return db.query(User).all()

# --- TEST VERIFICATION / E2E AUTO FLOW ---
@app.post("/api/demo/start-sequence")
def run_auto_demo_inspection(db: Session = Depends(get_db)):
    """
    Executes the E2E verification loop with a single request.
    Picks a sample -> starts workflow -> captures -> OCR -> evaluates.
    Returns complete final output report details.
    """
    # Pick a pending sample from high risk lot
    sample = db.query(Sample).join(Lot).filter(Sample.status == "PENDING", Lot.risk_score >= 60.0).first()
    if not sample:
        # Fallback to any pending sample
        sample = db.query(Sample).filter(Sample.status == "PENDING").first()
        
    if not sample:
        # Create a mock pending sample to avoid failure
        lot = db.query(Lot).first()
        sample = Sample(lot_id=lot.id, serial_number="SMP-DEMO-AUTO-9999", status="PENDING")
        db.add(sample)
        db.commit()
        db.refresh(sample)

    # 1. Start Inspection
    # Assign to admin user (id=4)
    insp = Inspection(
        sample_id=sample.id,
        officer_id=4,
        status="IN_PROGRESS",
        overall_compliance="PENDING"
    )
    db.add(insp)
    sample.status = "CAPTURED"
    db.commit()
    db.refresh(insp)

    # 2. Capture views
    views = camera_provider.capture_views(sample.lot.product.barcode, session_id=str(insp.id), force_perfect=True)
    for view in views:
        img = CapturedImage(
            inspection_id=insp.id,
            camera_view=view["camera_view"],
            image_path=view["image_path"],
            quality_status="GOOD"  # Force GOOD quality check pass
        )
        db.add(img)
    db.commit()

    # 3. Product Identification (already completed via SQL mapping)

    # 4. OCR & extraction
    run_packaging_ocr(insp.id, db)

    # 5. Evaluate compliance
    res = run_compliance_evaluation(insp.id, db)
    
    # 6. Save decision details (Pass/Fail)
    final_decision = "PASS" if res["overall_compliance"] == "COMPLIANT" else "FAIL"
    decision_notes = "Auto-evaluated through SIH inspection algorithm verification."
    
    submit_inspection_decision(
        id=insp.id,
        decision_req=InspectionDecisionRequest(final_decision=final_decision, notes=decision_notes),
        db=db,
        current_user=db.query(User).filter(User.id == 4).first()
    )

    return {
        "message": "Complete E2E Demonstration Loop completed successfully.",
        "inspection_id": insp.id,
        "sample_number": sample.serial_number,
        "product_name": sample.lot.product.name,
        "compliance": res["overall_compliance"],
        "verdict": final_decision
    }
