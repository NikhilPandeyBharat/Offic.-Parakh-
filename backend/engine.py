import datetime
from sqlalchemy.orm import Session
from backend.models import (
    Manufacturer, Product, Inspection, Violation, ProductVersion, CorrectiveAction,
    LegalRule, RuleVersion, ExtractedFact, Sample, Lot
)

class ExplainableRiskEngine:
    @staticmethod
    def calculate_manufacturer_risk(db: Session, manufacturer_id: int) -> dict:
        """
        Calculates a transparent, explainable risk score for a manufacturer
        based on historical compliance, repeat violations, packaging changes,
        and successful corrective actions.
        Returns:
            {
                "score": float, # 0 to 100
                "classification": str, # CRITICAL, HIGH, MEDIUM, LOW
                "factors": [
                    {"factor_name": str, "weight": float, "value": float, "calculated_impact": float}
                ]
            }
        """
        mfg = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
        if not mfg:
            return {"score": 10.0, "classification": "LOW", "factors": []}

        # Query stats
        mfg_products = db.query(Product).filter(Product.manufacturer_id == manufacturer_id).all()
        prod_ids = [p.id for p in mfg_products]

        total_insps = db.query(Inspection).join(Sample, Inspection.sample_id == Sample.id).join(Lot, Sample.lot_id == Lot.id).filter(Lot.product_id.in_(prod_ids)).count() if prod_ids else 0
        
        inspections = []
        if prod_ids:
            inspections = db.query(Inspection).join(Sample, Inspection.sample_id == Sample.id).join(Lot, Sample.lot_id == Lot.id).filter(Lot.product_id.in_(prod_ids)).all()

        violations_count = db.query(Violation).join(Inspection).join(Sample, Inspection.sample_id == Sample.id).join(Lot, Sample.lot_id == Lot.id).filter(Lot.product_id.in_(prod_ids)).count() if prod_ids else 0
        
        # Repeat violations (same product failing > 1 time)
        prod_fails = {}
        for insp in inspections:
            if insp.overall_compliance == "NON_COMPLIANT":
                pid = insp.sample.lot.product_id
                prod_fails[pid] = prod_fails.get(pid, 0) + 1
        repeat_violations = sum(1 for pid, fails in prod_fails.items() if fails > 1)

        # Packaging changes
        pkg_versions = db.query(ProductVersion).filter(ProductVersion.product_id.in_(prod_ids)).count() if prod_ids else 0

        # Recent failure within 30 days
        recent_fail = False
        thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        for insp in inspections:
            if insp.overall_compliance == "NON_COMPLIANT" and insp.timestamp >= thirty_days_ago:
                recent_fail = True
                break

        # Successful corrective actions
        resolved_actions = db.query(CorrectiveAction).filter(
            CorrectiveAction.manufacturer_id == manufacturer_id,
            CorrectiveAction.status == "RESOLVED"
        ).count()

        # Weighted Formula Factors
        # 1. Previous Violations: +3 per violation, max +30
        prev_viol_val = float(violations_count)
        prev_viol_impact = min(30.0, prev_viol_val * 3.0)

        # 2. Repeat Violations: +8 per repeat offender product, max +25
        repeat_val = float(repeat_violations)
        repeat_impact = min(25.0, repeat_val * 8.0)

        # 3. Category Risk Weight: average base risk weight of products, max +15
        if mfg_products:
            cat_val = sum(p.category.base_risk_weight for p in mfg_products) / len(mfg_products)
        else:
            cat_val = 10.0
        cat_impact = min(15.0, cat_val)

        # 4. Packaging Change Weight: +2 per change, max +10 (signifies volatility in labelling)
        pkg_val = float(pkg_versions)
        pkg_impact = min(10.0, pkg_val * 2.0)

        # 5. Recent Failure (within 30 days): +20
        recent_val = 1.0 if recent_fail else 0.0
        recent_impact = 20.0 if recent_fail else 0.0

        # 6. Successful Corrective Actions: -5 per resolution, subtracts risk
        resolved_val = float(resolved_actions)
        resolved_impact = -min(20.0, resolved_val * 5.0)

        # Total Risk Calculation
        raw_score = prev_viol_impact + repeat_impact + cat_impact + pkg_impact + recent_impact + resolved_impact
        final_score = min(100.0, max(0.0, raw_score))

        # Classification
        if final_score >= 80.0:
            classification = "CRITICAL"
        elif final_score >= 60.0:
            classification = "HIGH"
        elif final_score >= 40.0:
            classification = "MEDIUM"
        else:
            classification = "LOW"

        factors = [
            {"factor_name": "Previous Violations", "weight": 3.0, "value": prev_viol_val, "calculated_impact": prev_viol_impact},
            {"factor_name": "Repeat Violations", "weight": 8.0, "value": repeat_val, "calculated_impact": repeat_impact},
            {"factor_name": "Category Risk Weight", "weight": 1.0, "value": cat_val, "calculated_impact": cat_impact},
            {"factor_name": "Packaging Changes", "weight": 2.0, "value": pkg_val, "calculated_impact": pkg_impact},
            {"factor_name": "Recent Inspection Failures", "weight": 20.0, "value": recent_val, "calculated_impact": recent_impact},
            {"factor_name": "Successful Corrective Actions", "weight": -5.0, "value": resolved_val, "calculated_impact": resolved_impact}
        ]

        return {
            "score": round(final_score, 1),
            "classification": classification,
            "factors": factors
        }

class LegalComplianceEngine:
    @staticmethod
    def evaluate_compliance(db: Session, inspection_id: int) -> dict:
        """
        Runs the statutory A vs B evaluation:
        Compare extracted/observed facts (A) against active rule requirements (B).
        
        Returns:
            {
                "overall_compliance": str, # COMPLIANT, NON_COMPLIANT, REQUIRES_VERIFICATION
                "overall_coverage": float, # Percentage of checks completed
                "rules_matrix": [
                    {
                        "rule_code": str,
                        "title": str,
                        "severity": str,
                        "status": str, # COMPLIANT, NON_COMPLIANT, REQUIRES_VERIFICATION
                        "observed_value": str,
                        "confidence": float,
                        "notes": str
                    }
                ]
            }
        """
        # Fetch all facts extracted for this inspection
        facts = db.query(ExtractedFact).filter(ExtractedFact.inspection_id == inspection_id).all()
        facts_dict = {f.field_name: f for f in facts}

        # Fetch active rule versions
        rule_versions = db.query(RuleVersion).filter(RuleVersion.is_active == True).all()

        rules_matrix = []
        coverage_count = 0
        non_compliant_count = 0
        requires_verification_count = 0

        for rv in rule_versions:
            rule = rv.rule
            code = rule.rule_code

            status = "COMPLIANT"
            notes = "Statutory declaration detected and verified."
            observed_val = "Not Detected"
            confidence = 100.0

            # Match rules to specific extracted facts
            if code == "RULE-DEMO-001":  # MRP
                fact = facts_dict.get("mrp")
                if fact:
                    observed_val = fact.extracted_value
                    confidence = fact.confidence
                    if fact.normalized_value == "None" or "Not" in fact.extracted_value or fact.extracted_value.strip() == "":
                        status = "NON_COMPLIANT"
                        notes = "Maximum Retail Price (MRP) declaration is missing or unreadable."
                    elif fact.confidence < 60.0:
                        status = "REQUIRES_VERIFICATION"
                        notes = "MRP text detected but scanning confidence is too low."
                else:
                    status = "NON_COMPLIANT"
                    notes = "MRP declaration was not found on the packaging views."

            elif code == "RULE-DEMO-002":  # Net Qty
                fact = facts_dict.get("net_qty")
                if fact:
                    observed_val = fact.extracted_value
                    confidence = fact.confidence
                    if fact.normalized_value == "None" or "Not" in fact.extracted_value or fact.extracted_value.strip() == "":
                        status = "NON_COMPLIANT"
                        notes = "Net Quantity declaration is missing."
                    elif fact.confidence < 60.0:
                        status = "REQUIRES_VERIFICATION"
                        notes = "Net Quantity detected with low scanning confidence."
                else:
                    status = "NON_COMPLIANT"
                    notes = "Net Quantity declaration was not found."

            elif code == "RULE-DEMO-003":  # Manufacturer details
                fact = facts_dict.get("manufacturer_name")
                if fact:
                    observed_val = fact.extracted_value
                    confidence = fact.confidence
                    if fact.normalized_value == "None" or "Not" in fact.extracted_value or fact.extracted_value.strip() == "":
                        status = "NON_COMPLIANT"
                        notes = "Manufacturer name and address not found."
                    elif fact.confidence < 50.0:
                        status = "REQUIRES_VERIFICATION"
                        notes = "Manufacturer text detected with low confidence."
                else:
                    status = "NON_COMPLIANT"
                    notes = "Manufacturer identity details missing on label."

            elif code == "RULE-DEMO-004":  # Consumer Care
                fact = facts_dict.get("consumer_care_phone")
                if fact:
                    observed_val = fact.extracted_value
                    confidence = fact.confidence
                    if fact.normalized_value == "None" or "Not" in fact.extracted_value or fact.extracted_value.strip() == "":
                        status = "NON_COMPLIANT"
                        notes = "Consumer Helpline contact phone/email is missing."
                    elif fact.confidence < 60.0:
                        status = "REQUIRES_VERIFICATION"
                        notes = "Consumer care Helpline detected with low confidence."
                else:
                    status = "NON_COMPLIANT"
                    notes = "Consumer helpline declaration is missing."

            elif code == "RULE-DEMO-005":  # Month & Year of Packing
                fact = facts_dict.get("packed_date")
                if fact:
                    observed_val = fact.extracted_value
                    confidence = fact.confidence
                    if fact.normalized_value == "None" or "Not" in fact.extracted_value or fact.extracted_value.strip() == "":
                        status = "NON_COMPLIANT"
                        notes = "Month and Year of packing declaration is missing."
                    elif fact.confidence < 60.0:
                        status = "REQUIRES_VERIFICATION"
                        notes = "Packing date detected with low confidence."
                else:
                    status = "NON_COMPLIANT"
                    notes = "Month and Year of packing not found."

            elif code == "RULE-DEMO-006":  # Country of Origin
                fact = facts_dict.get("country_of_origin")
                if fact:
                    observed_val = fact.extracted_value
                    confidence = fact.confidence
                    if fact.normalized_value == "None" or "Not" in fact.extracted_value or fact.extracted_value.strip() == "":
                        status = "NON_COMPLIANT"
                        notes = "Country of origin declaration is missing."
                    elif fact.confidence < 50.0:
                        status = "REQUIRES_VERIFICATION"
                        notes = "Country of origin detected with low confidence."
                else:
                    # Let's say if country of origin is missing, we flag it as a minor check
                    status = "NON_COMPLIANT"
                    notes = "Country of origin not found."

            rules_matrix.append({
                "rule_version_id": rv.id,
                "rule_code": code,
                "title": rule.title,
                "severity": rule.severity,
                "status": status,
                "observed_value": observed_val,
                "confidence": round(confidence, 1),
                "notes": f"DEMO RULE - {notes}"
            })

            if status != "PENDING":
                coverage_count += 1
            if status == "NON_COMPLIANT":
                non_compliant_count += 1
            if status == "REQUIRES_VERIFICATION":
                requires_verification_count += 1

        overall_coverage = (coverage_count / len(rule_versions)) * 100.0 if rule_versions else 0.0
        
        # Overall status is NOT a simple 95% pass percentage
        # If any rule is NON_COMPLIANT, overall is NON_COMPLIANT
        # If there are no violations, but some are REQUIRES_VERIFICATION, overall is REQUIRES_VERIFICATION
        # Else COMPLIANT
        if non_compliant_count > 0:
            overall_compliance = "NON_COMPLIANT"
        elif requires_verification_count > 0:
            overall_compliance = "REQUIRES_VERIFICATION"
        else:
            overall_compliance = "COMPLIANT"

        return {
            "overall_compliance": overall_compliance,
            "overall_coverage": round(overall_coverage, 1),
            "rules_matrix": rules_matrix
        }
