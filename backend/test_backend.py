import os
from backend.database import SessionLocal
from backend.models import User, Manufacturer, Product, Inspection, ExtractedFact
from backend.engine import ExplainableRiskEngine, LegalComplianceEngine
from backend.report import generate_inspection_report
from backend.auth import get_password_hash, verify_password

def run_tests():
    print("--- Running PARAKH Backend Tests ---")
    db = SessionLocal()
    try:
        # Test 1: User authentication
        print("Test 1: Verifying user auth hashing...")
        raw_pwd = "operator123"
        hashed = get_password_hash(raw_pwd)
        assert verify_password(raw_pwd, hashed) is True
        assert verify_password("wrong_password", hashed) is False
        print("Pass: User password hashing is correct.")

        # Test 2: Database seeding
        print("Test 2: Verifying seeded tables...")
        users_count = db.query(User).count()
        mfg_count = db.query(Manufacturer).count()
        prod_count = db.query(Product).count()
        print(f"Seed count: Users={users_count}, Manufacturers={mfg_count}, Products={prod_count}")
        assert users_count >= 4
        assert mfg_count >= 30
        assert prod_count >= 40
        print("Pass: Seeding verification matches minimum metrics.")

        # Test 3: Explainable Risk Engine
        print("Test 3: Verifying Risk Score Calculation...")
        mfg = db.query(Manufacturer).first()
        risk_result = ExplainableRiskEngine.calculate_manufacturer_risk(db, mfg.id)
        print(f"Risk evaluation for {mfg.name}: Score={risk_result['score']} ({risk_result['classification']})")
        assert 0.0 <= risk_result["score"] <= 100.0
        print("Pass: Explainable Risk Engine executed correctly.")

        # Test 4: Legal Compliance Engine
        print("Test 4: Verifying Compliance Engine...")
        insp = db.query(Inspection).first()
        comp_result = LegalComplianceEngine.evaluate_compliance(db, insp.id)
        print(f"Compliance status for Inspection {insp.id}: Status={comp_result['overall_compliance']}, Coverage={comp_result['overall_coverage']}%")
        assert comp_result["overall_compliance"] in ["COMPLIANT", "NON_COMPLIANT", "REQUIRES_VERIFICATION"]
        print("Pass: Legal Compliance Engine executed correctly.")

        # Test 5: Report generation
        print("Test 5: Verifying PDF Report Generation...")
        output_pdf = "backend/static/reports/test_report.pdf"
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        generate_inspection_report(db, insp.id, output_pdf)
        assert os.path.exists(output_pdf) is True
        print(f"Pass: PDF report successfully generated at {output_pdf}")
        
        print("\n--- ALL BACKEND TESTS PASSED SUCCESSFULLY! ---")

    except Exception as e:
        print(f"FAIL: Backend tests crashed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
