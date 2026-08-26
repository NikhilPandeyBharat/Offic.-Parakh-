from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Auth Schemas
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str

    class Config:
        from_attributes = True

# Manufacturer Schemas
class ManufacturerResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    risk_score: float
    last_inspection_date: Optional[datetime]
    compliance_rate: float

    class Config:
        from_attributes = True

# Category Schemas
class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    base_risk_weight: float

    class Config:
        from_attributes = True

# Product Schemas
class ProductResponse(BaseModel):
    id: int
    name: str
    barcode: str
    manufacturer_id: int
    category_id: int
    current_version: str
    status: str
    manufacturer: Optional[ManufacturerResponse] = None
    category: Optional[ProductCategoryResponse] = None

    class Config:
        from_attributes = True

class ProductVersionResponse(BaseModel):
    id: int
    product_id: int
    version_number: str
    packaging_hash: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Shipment Schemas
class ShipmentResponse(BaseModel):
    id: int
    shipment_number: str
    date_received: datetime
    status: str
    lot_count: int
    item_count: int

    class Config:
        from_attributes = True

class LotResponse(BaseModel):
    id: int
    shipment_id: int
    product_id: int
    quantity: int
    risk_score: float
    priority_status: str
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class ShipmentDetailResponse(ShipmentResponse):
    lots: List[LotResponse] = []

    class Config:
        from_attributes = True

# Sample Schemas
class SampleResponse(BaseModel):
    id: int
    lot_id: int
    serial_number: str
    status: str
    lot: Optional[LotResponse] = None

    class Config:
        from_attributes = True

# Captured Image Schemas
class CapturedImageResponse(BaseModel):
    id: int
    inspection_id: int
    camera_view: str
    image_path: str
    quality_status: str
    captured_at: datetime

    class Config:
        from_attributes = True

class RecaptureRequest(BaseModel):
    camera_view: str

# OCR Result & Facts
class OCRResultResponse(BaseModel):
    id: int
    captured_image_id: int
    field_name: Optional[str]
    raw_text: str
    confidence: float
    bounding_box: Optional[str]

    class Config:
        from_attributes = True

class ExtractedFactResponse(BaseModel):
    id: int
    inspection_id: int
    field_name: str
    extracted_value: Optional[str]
    normalized_value: Optional[str]
    confidence: float
    source_image_id: Optional[int]

    class Config:
        from_attributes = True

class FactEditRequest(BaseModel):
    field_name: str
    edited_value: str

# Legal Rule & Compliance
class RuleVersionResponse(BaseModel):
    id: int
    rule_id: int
    version: int
    effective_date: datetime
    validation_criteria: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class LegalRuleResponse(BaseModel):
    id: int
    rule_code: str
    title: str
    description: Optional[str]
    severity: str
    versions: List[RuleVersionResponse] = []

    class Config:
        from_attributes = True

class RuleCreateRequest(BaseModel):
    rule_code: str
    title: str
    description: str
    severity: str
    category_id: Optional[int] = None

class ComplianceEvaluationResponse(BaseModel):
    id: int
    inspection_id: int
    rule_version_id: int
    status: str
    notes: Optional[str]
    rule_version: Optional[RuleVersionResponse] = None

    class Config:
        from_attributes = True

class ViolationResponse(BaseModel):
    id: int
    inspection_id: int
    rule_version_id: int
    fact_id: Optional[int]
    severity: str
    description: Optional[str]

    class Config:
        from_attributes = True

class EvidenceResponse(BaseModel):
    id: int
    inspection_id: int
    type: str
    file_path: Optional[str]
    bounding_box: Optional[str]
    confidence: float

    class Config:
        from_attributes = True

# Inspection Detail Response
class InspectionResponse(BaseModel):
    id: int
    sample_id: int
    officer_id: Optional[int]
    timestamp: datetime
    status: str
    overall_coverage: float
    overall_compliance: str
    final_decision: Optional[str]
    notes: Optional[str]
    sample: Optional[SampleResponse] = None
    captured_images: List[CapturedImageResponse] = []
    extracted_facts: List[ExtractedFactResponse] = []
    compliance_evaluations: List[ComplianceEvaluationResponse] = []
    violations: List[ViolationResponse] = []
    evidence: List[EvidenceResponse] = []

    class Config:
        from_attributes = True

class InspectionDecisionRequest(BaseModel):
    final_decision: str  # PASS, FAIL, RE-INSPECT, PROSECUTE
    notes: Optional[str] = None
    verify_findings: Optional[List[dict]] = None  # Accept/Reject list

# Corrective Actions & Reinspections
class CorrectiveActionResponse(BaseModel):
    id: int
    inspection_id: int
    manufacturer_id: int
    product_id: int
    date_issued: datetime
    due_date: Optional[datetime]
    status: str
    notes: Optional[str]
    manufacturer: Optional[ManufacturerResponse] = None
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class CorrectiveActionCreateRequest(BaseModel):
    inspection_id: int
    due_days: int = 30
    notes: Optional[str] = None

class CorrectiveActionUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class ReinspectionResponse(BaseModel):
    id: int
    original_inspection_id: int
    corrective_action_id: int
    new_inspection_id: Optional[int]
    status: str
    comparison_result: Optional[str]
    corrective_action: Optional[CorrectiveActionResponse] = None

    class Config:
        from_attributes = True

class ReinspectionScheduleRequest(BaseModel):
    corrective_action_id: int

# Risk Scores & Factors
class RiskFactorResponse(BaseModel):
    id: int
    risk_score_id: int
    factor_name: str
    weight: float
    value: float

    class Config:
        from_attributes = True

class RiskScoreResponse(BaseModel):
    id: int
    target_type: str
    target_id: int
    score: float
    updated_at: datetime
    factors: List[RiskFactorResponse] = []

    class Config:
        from_attributes = True

# Recommendations
class RecommendationResponse(BaseModel):
    id: int
    target_type: str
    target_id: int
    action: str
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True

# Investigation Case
class InvestigationCaseResponse(BaseModel):
    id: int
    case_number: str
    manufacturer_id: int
    product_id: int
    shipment_id: Optional[int]
    status: str
    risk_level: str
    notes: Optional[str]
    created_at: datetime
    manufacturer: Optional[ManufacturerResponse] = None
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class CaseCreateRequest(BaseModel):
    manufacturer_id: int
    product_id: int
    shipment_id: Optional[int] = None
    risk_level: str
    notes: Optional[str] = None

class CaseUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None

# Audit Log
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    timestamp: datetime
    details: Optional[str]
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
