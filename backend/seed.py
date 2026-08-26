import datetime
import random
from sqlalchemy.orm import Session
from backend.database import engine, Base, SessionLocal
from backend.models import (
    User, Manufacturer, ProductCategory, Product, ProductVersion, Shipment, Lot, Sample,
    Inspection, CapturedImage, OCRResult, ExtractedFact, LegalRule, RuleVersion,
    ComplianceEvaluation, Violation, Evidence, CorrectiveAction, Reinspection,
    RiskScore, RiskFactor, Recommendation, AuditLog, InvestigationCase
)
from backend.auth import get_password_hash

def seed_db():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("Seeding Users...")
        users = [
            User(username="operator", password_hash=get_password_hash("operator123"), role="CAPTURE_OPERATOR", full_name="Ramesh Kumar (Operator)"),
            User(username="verification", password_hash=get_password_hash("verification123"), role="VERIFICATION_OFFICER", full_name="Anjali Sharma (Verification Officer)"),
            User(username="enforcement", password_hash=get_password_hash("enforcement123"), role="SENIOR_ENFORCEMENT_OFFICER", full_name="Director-General D. K. Gupta"),
            User(username="admin", password_hash=get_password_hash("admin123"), role="ADMIN", full_name="System Administrator"),
        ]
        db.add_all(users)
        db.commit()

        print("Seeding Product Categories...")
        categories_data = [
            ("Packaged Food", "Biscuits, snacks, flour, spices, grains, ready-to-eat meals.", 15.0),
            ("Cosmetics", "Soaps, shampoos, face washes, creams, makeup items.", 12.0),
            ("Electronics", "Laptops, phones, chargers, smart devices, batteries.", 8.0),
            ("Beverages", "Juices, soft drinks, packaged drinking water, milk shakes.", 15.0),
            ("Household Products", "Detergents, cleaning liquids, room fresheners, dishwashing bars.", 10.0),
            ("Pharmaceuticals", "Over-the-counter drugs, health supplements, syrups, tablets.", 20.0),
            ("Dairy", "Cheese, butter, paneer, packaged milk, yogurt.", 18.0),
            ("Snacks", "Potato chips, namkeen, chocolates, candy packs.", 12.0),
            ("Apparel", "Packaged garments, socks, innerwear, bedsheets.", 5.0),
            ("Personal Care", "Toothpastes, toothbrushes, hand sanitizers, shaving gels.", 10.0)
        ]
        categories = []
        for name, desc, risk in categories_data:
            cat = ProductCategory(name=name, description=desc, base_risk_weight=risk)
            db.add(cat)
            categories.append(cat)
        db.commit()

        print("Seeding Legal Rules...")
        # Create standard metrology declarations rules
        rules_data = [
            ("RULE-DEMO-001", "MRP Declaration Required", "The retail sale price of the package shall be clearly declared in the form 'Maximum Retail Price Rs... / ₹...' or 'MRP Rs... / ₹...' inclusive of all taxes.", "Packaged Food", "CRITICAL"),
            ("RULE-DEMO-002", "Net Quantity Declaration Required", "The net quantity, in terms of standard unit of weight or measure or number, shall be declared on the package.", "Packaged Food", "CRITICAL"),
            ("RULE-DEMO-003", "Manufacturer / Packer / Importer Details", "The name and complete address of the manufacturer, packer, or importer must be declared on every package.", "Packaged Food", "MAJOR"),
            ("RULE-DEMO-004", "Consumer Care Contact Information", "Every package shall contain the name, address, telephone number, and e-mail address of the person or office that can be contacted in case of consumer complaints.", "Packaged Food", "MAJOR"),
            ("RULE-DEMO-005", "Month and Year of Packing/Manufacturing", "The month and year in which the commodity is manufactured, packed, or imported shall be declared.", "Packaged Food", "MAJOR"),
            ("RULE-DEMO-006", "Country of Origin (for imported commodities)", "The name of the country of origin must be declared on the package if the commodity is imported.", "Packaged Food", "MINOR"),
        ]
        rules = []
        for code, title, desc, cat_name, sev in rules_data:
            # Connect rules to the first category as default, but in engine they are checked based on applicability
            rule = LegalRule(rule_code=code, title=title, description=f"DEMO RULE - {desc}", severity=sev)
            db.add(rule)
            db.flush()
            version = RuleVersion(rule_id=rule.id, version=1, is_active=True, validation_criteria=f"Checks presence of {title.split()[0]} declaration")
            db.add(version)
            rules.append(rule)
        db.commit()

        print("Seeding Manufacturers...")
        manufacturers_data = [
            ("Apex Foods Ltd", "MFG-APEX-001", "12, Industrial Area, Sector 5", "Gurugram", "Haryana"),
            ("Bharti Cosmetics Ltd", "MFG-BHAR-002", "Block C, Okhla Phase III", "New Delhi", "Delhi"),
            ("Cybertonics India", "MFG-CYBE-003", "IT Park, Whitefield", "Bengaluru", "Karnataka"),
            ("Deccan Breweries & Beverages", "MFG-DECC-004", "MIDC Industrial Estate", "Pune", "Maharashtra"),
            ("Elixir Pharmaceuticals", "MFG-ELIX-005", "Baddi Industrial Zone", "Solan", "Himachal Pradesh"),
            ("Frosty Dairy Foods", "MFG-FROS-006", "Dairy Road", "Anand", "Gujarat"),
            ("Giga Appliances Corp", "MFG-GIGA-007", "GIDC Electronic City", "Gandhinagar", "Gujarat"),
            ("Highland Apparel Co", "MFG-HIGH-008", "Tirupur Garment Park", "Tirupur", "Tamil Nadu"),
            ("Indus Organics", "MFG-INDU-009", "Organic Farm Road", "Haridwar", "Uttarakhand"),
            ("Jupiter Soaps & Detergents", "MFG-JUPI-010", "Verna Industrial Estate", "Salcete", "Goa"),
            ("Kalinga Mills", "MFG-KALI-011", "Cuttack Road", "Bhubaneswar", "Odisha"),
            ("Laxmi Flour & Grains", "MFG-LAXM-012", "APMC Market", "Indore", "Madhya Pradesh"),
            ("Medica Biotech", "MFG-MEDI-013", "Genome Valley", "Hyderabad", "Telangana"),
            ("Narmada Dairy", "MFG-NARM-014", "Narmada Marg", "Jabalpur", "Madhya Pradesh"),
            ("Orient Confectionery", "MFG-ORIE-015", "Taratala Road", "Kolkata", "West Bengal"),
            ("Pioneer Foods India", "MFG-PION-016", "Loni Kalbhor", "Pune", "Maharashtra"),
            ("QuickClean Household products", "MFG-QUIC-017", "RIICO Area", "Jaipur", "Rajasthan"),
            ("Ratan Textiles", "MFG-RATA-018", "Sanganer", "Jaipur", "Rajasthan"),
            ("Sun Beverages", "MFG-SUNB-019", "Industrial Suburb", "Mysuru", "Karnataka"),
            ("Tulsi Spices & Herbs", "MFG-TULS-020", "Spices Park", "Guntur", "Andhra Pradesh"),
            ("United Packers & Logistics", "MFG-UNIT-021", "JNPT Area", "Navi Mumbai", "Maharashtra"),
            ("Vedic Health Products", "MFG-VEDI-022", "Patanjali Yogpeeth", "Haridwar", "Uttarakhand"),
            ("Western Salt & Spices", "MFG-WEST-023", "Mundra Port Road", "Kutch", "Gujarat"),
            ("Xenon Electronics", "MFG-XENO-024", "SEZ Zone", "Noida", "Uttar Pradesh"),
            ("Yummy Snacks Pvt Ltd", "MFG-YUMM-025", "Sinnar MIDC", "Nashik", "Maharashtra"),
            ("Zest Personal Care", "MFG-ZEST-026", "Piparia Industrial Estate", "Silvassa", "Dadra and Nagar Haveli"),
            ("Nirmaan Industries", "MFG-NIRM-027", "Asarwa", "Ahmedabad", "Gujarat"),
            ("Hindustan Food & Allied", "MFG-HIND-028", "Majitar", "Rangpo", "Sikkim"),
            ("Godavari Agri Products", "MFG-GODA-029", "Rajamahendravaram", "East Godavari", "Andhra Pradesh"),
            ("Royal Breweries", "MFG-ROYA-030", "Industrial Area", "Samba", "Jammu and Kashmir")
        ]
        manufacturers = []
        for name, code, addr, city, state in manufacturers_data:
            mfg = Manufacturer(name=name, code=code, address=addr, city=city, state=state, risk_score=random.uniform(10, 85), compliance_rate=random.uniform(70, 100))
            db.add(mfg)
            manufacturers.append(mfg)
        db.commit()

        print("Seeding Products...")
        products_data = [
            ("Apex Digestive Biscuits 500g", "8901000000001", "Apex Foods Ltd", "Packaged Food"),
            ("Apex Choco Chip Cookies 150g", "8901000000002", "Apex Foods Ltd", "Packaged Food"),
            ("Bharti Moisturizing Cream 200ml", "8901000000003", "Bharti Cosmetics Ltd", "Cosmetics"),
            ("Bharti Lavender Soap 100g", "8901000000004", "Bharti Cosmetics Ltd", "Cosmetics"),
            ("Cybertonics Powerbank 10000mAh", "8901000000005", "Cybertonics India", "Electronics"),
            ("Cybertonics USB-C Cable 1.5m", "8901000000006", "Cybertonics India", "Electronics"),
            ("Deccan Premium Pilsner Beer 650ml", "8901000000007", "Deccan Breweries & Beverages", "Beverages"),
            ("Deccan Apple Juice 1L", "8901000000008", "Deccan Breweries & Beverages", "Beverages"),
            ("Elixir Multivitamin Tablets 30s", "8901000000009", "Elixir Pharmaceuticals", "Pharmaceuticals"),
            ("Elixir Cough Syrup 100ml", "8901000000010", "Elixir Pharmaceuticals", "Pharmaceuticals"),
            ("Frosty Butter 500g", "8901000000011", "Frosty Dairy Foods", "Dairy"),
            ("Frosty Premium Cheese Slices 200g", "8901000000012", "Frosty Dairy Foods", "Dairy"),
            ("Giga Smart LED Bulb 9W", "8901000000013", "Giga Appliances Corp", "Electronics"),
            ("Highland Cotton Socks Pack of 3", "8901000000014", "Highland Apparel Co", "Apparel"),
            ("Indus Organic Honey 250g", "8901000000015", "Indus Organics", "Packaged Food"),
            ("Jupiter Liquid Detergent 1L", "8901000000016", "Jupiter Soaps & Detergents", "Household Products"),
            ("Kalinga Basmati Rice 5kg", "8901000000017", "Kalinga Mills", "Packaged Food"),
            ("Laxmi Premium Atta 10kg", "8901000000018", "Laxmi Flour & Grains", "Packaged Food"),
            ("Medica Pain Relief Gel 30g", "8901000000019", "Medica Biotech", "Pharmaceuticals"),
            ("Narmada Full Cream Milk 1L", "8901000000020", "Narmada Dairy", "Dairy"),
            ("Orient Strawberry Wafers 75g", "8901000000021", "Orient Confectionery", "Snacks"),
            ("Pioneer Refined Sunflower Oil 1L", "8901000000022", "Pioneer Foods India", "Packaged Food"),
            ("QuickClean Floor Cleaner 500ml", "8901000000023", "QuickClean Household products", "Household Products"),
            ("Ratan Designer Bedsheet Double", "8901000000024", "Ratan Textiles", "Apparel"),
            ("Sun Sparkling Soda 300ml", "8901000000025", "Sun Beverages", "Beverages"),
            ("Tulsi Red Chilli Powder 200g", "8901000000026", "Tulsi Spices & Herbs", "Packaged Food"),
            ("Vedic Chyawanprash 500g", "8901000000027", "Vedic Health Products", "Pharmaceuticals"),
            ("Western Iodized Salt 1kg", "8901000000028", "Western Salt & Spices", "Packaged Food"),
            ("Xenon Wireless Mouse WM100", "8901000000029", "Xenon Electronics", "Electronics"),
            ("Yummy Potato Chips Salted 50g", "8901000000030", "Yummy Snacks Pvt Ltd", "Snacks"),
            ("Zest Aloe Vera Gel 150g", "8901000000031", "Zest Personal Care", "Personal Care"),
            ("Nirmaan Detergent Powder 2kg", "8901000000032", "Nirmaan Industries", "Household Products"),
            ("Hindustan Pure Ghee 1L", "8901000000033", "Hindustan Food & Allied", "Dairy"),
            ("Godavari Raw Rice 10kg", "8901000000034", "Godavari Agri Products", "Packaged Food"),
            ("Royal Strong Beer 650ml", "8901000000035", "Royal Breweries", "Beverages"),
            ("Apex Roasted Cashews 200g", "8901000000036", "Apex Foods Ltd", "Snacks"),
            ("Bharti Sunscreen Lotion SPF50", "8901000000037", "Bharti Cosmetics Ltd", "Cosmetics"),
            ("Elixir Vitamin C Drops 50ml", "8901000000038", "Elixir Pharmaceuticals", "Pharmaceuticals"),
            ("Jupiter Dishwash Liquid 250ml", "8901000000039", "Jupiter Soaps & Detergents", "Household Products"),
            ("Yummy Chocolate Cookies 200g", "8901000000040", "Yummy Snacks Pvt Ltd", "Snacks")
        ]
        products = []
        for name, barcode, mfg_name, cat_name in products_data:
            mfg = next(m for m in manufacturers if m.name == mfg_name)
            cat = next(c for c in categories if c.name == cat_name)
            prod = Product(name=name, barcode=barcode, manufacturer_id=mfg.id, category_id=cat.id, current_version="v1", status="ACTIVE")
            db.add(prod)
            db.flush()

            # Create default packaging version
            pv = ProductVersion(
                product_id=prod.id,
                version_number="v1",
                packaging_hash="hash_v1_default",
                description="Initial market packaging layout."
            )
            db.add(pv)
            products.append(prod)
        db.commit()

        print("Seeding Shipments & Lots...")
        shipments = []
        for i in range(1, 51):
            date_received = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 150))
            shp = Shipment(
                shipment_number=f"SHP-2026-{i:06d}",
                date_received=date_received,
                status="INSPECTED" if i < 40 else "PENDING",
                lot_count=random.randint(2, 6),
                item_count=random.randint(5000, 200000)
            )
            db.add(shp)
            db.flush()
            shipments.append(shp)

            # Add lots for each shipment
            for j in range(shp.lot_count):
                prod = random.choice(products)
                quantity = random.randint(100, 5000)
                
                # Deterministic prototype risk score for initial load
                mfg = prod.manufacturer
                base_risk = prod.category.base_risk_weight
                mfg_risk = mfg.risk_score
                lot_risk = base_risk + (mfg_risk * 0.7) + (20.0 if mfg.compliance_rate < 85 else 0.0)
                lot_risk = min(100.0, max(0.0, lot_risk))
                
                priority = "LOW"
                if lot_risk >= 80: priority = "CRITICAL"
                elif lot_risk >= 60: priority = "HIGH"
                elif lot_risk >= 40: priority = "MEDIUM"

                lot = Lot(
                    shipment_id=shp.id,
                    product_id=prod.id,
                    quantity=quantity,
                    risk_score=lot_risk,
                    priority_status=priority
                )
                db.add(lot)
                db.flush()
                
                # Seed some samples for this lot
                for s in range(1, 4):
                    sample = Sample(
                        lot_id=lot.id,
                        serial_number=f"SMP-{shp.shipment_number[-4:]}-{lot.id}-{s}",
                        status="EVALUATED" if shp.status == "INSPECTED" else "PENDING"
                    )
                    db.add(sample)
        db.commit()

        print("Seeding Historical Inspections...")
        # We will seed 150 historical inspections
        # Out of these, ~110 will be PASS, ~30 will be FAIL, ~10 will be REVIEW
        inspected_samples = db.query(Sample).filter(Sample.status == "EVALUATED").all()
        random.shuffle(inspected_samples)
        
        # Pick subset of samples to attach inspections to
        active_officers = db.query(User).filter(User.role.in_(["CAPTURE_OPERATOR", "VERIFICATION_OFFICER"])).all()
        
        for idx, sample in enumerate(inspected_samples[:160]):
            officer = random.choice(active_officers)
            lot = sample.lot
            prod = lot.product
            mfg = prod.manufacturer

            # Determine compliance status of this sample
            # Make certain manufacturers high risk (Apex Foods, Deccan Breweries, Bharti Cosmetics)
            is_offender = mfg.name in ["Apex Foods Ltd", "Deccan Breweries & Beverages", "Bharti Cosmetics Ltd", "Royal Breweries"]
            
            if is_offender and random.random() < 0.65:
                # High risk offender, likely fail
                comp_status = "NON_COMPLIANT"
                decision = "FAIL"
                sample.status = "VIOLATION"
            elif random.random() < 0.15:
                comp_status = "REQUIRES_VERIFICATION"
                decision = "RE-INSPECT"
                sample.status = "REVIEW"
            else:
                comp_status = "COMPLIANT"
                decision = "PASS"
                sample.status = "COMPLIANT"

            insp = Inspection(
                sample_id=sample.id,
                officer_id=officer.id,
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(5, 120)),
                status="COMPLETED",
                overall_coverage=random.uniform(90.0, 100.0),
                overall_compliance=comp_status,
                final_decision=decision,
                notes=f"Routine legal metrology package analysis. Targeted checking of {prod.name}."
            )
            db.add(insp)
            db.flush()

            # Add captured images (simulated)
            cam_views = ["FRONT", "BACK", "LEFT", "RIGHT", "TOP"]
            images = []
            for view in cam_views:
                # Randomize image quality checks
                q_status = "GOOD"
                if view == "RIGHT" and random.random() < 0.08:
                    q_status = "GLARE"
                elif view == "LEFT" and random.random() < 0.04:
                    q_status = "BLUR"

                img = CapturedImage(
                    inspection_id=insp.id,
                    camera_view=view,
                    image_path=f"/static/images/demo/{prod.barcode}_{view.lower()}.jpg",
                    quality_status=q_status
                )
                db.add(img)
                db.flush()
                images.append(img)

            # Generate extracted facts
            facts = {
                "mrp": (f"MRP ₹{random.choice([150, 199, 249, 299])}.00", f"{random.choice([150, 199, 249, 299])} INR"),
                "net_qty": (f"NET QUANTITY: {random.choice([500, 250, 100])} g", f"{random.choice([500, 250, 100])} g"),
                "manufacturer_name": (f"Mfg by: {mfg.name}", mfg.name),
                "packed_date": ("Packed: 05/2026", "2026-05-01"),
                "consumer_care_phone": ("Helpline: 1800-000-0000", "18000000000"),
                "country_of_origin": ("Origin: India", "India")
            }

            fact_records = []
            for field, (raw, norm) in facts.items():
                # Let's simulate that some facts might be missing for failed inspections
                if comp_status == "NON_COMPLIANT" and field == "consumer_care_phone" and random.random() < 0.5:
                    # Missing consumer care phone
                    raw, norm = "Not detected", "None"
                if comp_status == "NON_COMPLIANT" and field == "mrp" and random.random() < 0.3:
                    # Missing MRP
                    raw, norm = "Price: nil", "None"

                fact = ExtractedFact(
                    inspection_id=insp.id,
                    field_name=field,
                    extracted_value=raw,
                    normalized_value=norm,
                    confidence=random.uniform(85, 99) if norm != "None" else 10.0,
                    source_image_id=random.choice(images).id
                )
                db.add(fact)
                db.flush()
                fact_records.append(fact)

            # Seed compliance evaluations and violations
            active_rules = db.query(RuleVersion).filter(RuleVersion.is_active == True).all()
            for rv in active_rules:
                rule_code = rv.rule.rule_code
                rule_status = "COMPLIANT"
                rule_note = "Evaluation matched statutory specifications."
                
                # Link rule failures
                failed_fact = None
                if comp_status == "NON_COMPLIANT":
                    if rule_code == "RULE-DEMO-004" and any(f.field_name == "consumer_care_phone" and f.normalized_value == "None" for f in fact_records):
                        rule_status = "NON_COMPLIANT"
                        rule_note = "Statutory declaration for customer helpline address/contact is missing."
                        failed_fact = next(f for f in fact_records if f.field_name == "consumer_care_phone")
                    elif rule_code == "RULE-DEMO-001" and any(f.field_name == "mrp" and f.normalized_value == "None" for f in fact_records):
                        rule_status = "NON_COMPLIANT"
                        rule_note = "Maximum retail price (MRP) is not specified or layout is non-compliant."
                        failed_fact = next(f for f in fact_records if f.field_name == "mrp")

                elif comp_status == "REQUIRES_VERIFICATION" and rule_code in ["RULE-DEMO-002", "RULE-DEMO-005"] and random.random() < 0.6:
                    rule_status = "REQUIRES_VERIFICATION"
                    rule_note = "Low OCR reading confidence, manual check required."

                eval_rec = ComplianceEvaluation(
                    inspection_id=insp.id,
                    rule_version_id=rv.id,
                    status=rule_status,
                    notes=rule_note
                )
                db.add(eval_rec)

                if rule_status == "NON_COMPLIANT":
                    violation = Violation(
                        inspection_id=insp.id,
                        rule_version_id=rv.id,
                        fact_id=failed_fact.id if failed_fact else None,
                        severity=rv.rule.severity,
                        description=rule_note
                    )
                    db.add(violation)
                    db.flush()
                    
                    # Add Evidence
                    ev = Evidence(
                        inspection_id=insp.id,
                        type="IMAGE",
                        file_path=random.choice(images).image_path,
                        bounding_box="120,450,300,80",
                        confidence=88.5,
                        rule_version_id=rv.id
                    )
                    db.add(ev)

        db.commit()

        print("Seeding Corrective Actions and Re-inspections...")
        failed_inspections = db.query(Inspection).filter(Inspection.overall_compliance == "NON_COMPLIANT").all()
        
        # Link corrective actions to around 70% of failed inspections
        for insp in failed_inspections:
            prod = insp.sample.lot.product
            mfg = prod.manufacturer

            if random.random() < 0.75:
                # Issue corrective action
                due_date = insp.timestamp + datetime.timedelta(days=30)
                status_choices = ["RESOLVED", "OPEN", "IN_PROGRESS", "OVERDUE", "FAILED"]
                
                # If inspection is older than 45 days, it should be resolved or failed.
                time_diff = (datetime.datetime.utcnow() - insp.timestamp).days
                if time_diff > 45:
                    act_status = random.choice(["RESOLVED", "FAILED"])
                else:
                    act_status = random.choice(["OPEN", "IN_PROGRESS", "OVERDUE"])

                notes = f"Corrective notice sent to {mfg.name} regarding packaging violations. Demand print revision layout."
                if act_status == "RESOLVED":
                    notes += " Manufacturer revised labeling and submitted compliance sample proof."
                elif act_status == "FAILED":
                    notes += " Manufacturer did not respond within period or print revisions were rejected."

                action = CorrectiveAction(
                    inspection_id=insp.id,
                    manufacturer_id=mfg.id,
                    product_id=prod.id,
                    date_issued=insp.timestamp + datetime.timedelta(days=2),
                    due_date=due_date,
                    status=act_status,
                    notes=notes
                )
                db.add(action)
                db.flush()

                # For some, create Re-inspection
                if act_status in ["RESOLVED", "FAILED"]:
                    # Create a reinspection log
                    reinsp = Reinspection(
                        original_inspection_id=insp.id,
                        corrective_action_id=action.id,
                        status="COMPLETED",
                        comparison_result="RESOLVED" if act_status == "RESOLVED" else "REPEATED_VIOLATION"
                    )
                    db.add(reinsp)
                    db.flush()

                    # Create the new re-inspection record
                    new_sample = db.query(Sample).filter(Sample.lot.has(product_id=prod.id), Sample.status == "PENDING").first()
                    if new_sample:
                        new_sample.status = "COMPLIANT" if act_status == "RESOLVED" else "VIOLATION"
                        
                        new_insp = Inspection(
                            sample_id=new_sample.id,
                            officer_id=insp.officer_id,
                            timestamp=insp.timestamp + datetime.timedelta(days=25),
                            status="COMPLETED",
                            overall_coverage=100.0,
                            overall_compliance="COMPLIANT" if act_status == "RESOLVED" else "NON_COMPLIANT",
                            final_decision="PASS" if act_status == "RESOLVED" else "PROSECUTE",
                            notes=f"Re-inspection under corrective notice action. Verification of packaging version revision."
                        )
                        db.add(new_insp)
                        db.flush()
                        
                        reinsp.new_inspection_id = new_insp.id
                        
                        # Add a ProductVersion if resolved
                        if act_status == "RESOLVED":
                            pv = ProductVersion(
                                product_id=prod.id,
                                version_number="v2",
                                packaging_hash="hash_v2_revised",
                                description="Revised packaging layout. Fixed MRP and consumer care details."
                            )
                            db.add(pv)
                            prod.current_version = "v2"
        db.commit()

        print("Recalculating Manufacturer & Product Risks...")
        # Now query manufacturer data and calculate actual risk score based on seeded history
        manufacturers = db.query(Manufacturer).all()
        for m in manufacturers:
            # Let's count violations and calculate stats
            mfg_products = db.query(Product).filter(Product.manufacturer_id == m.id).all()
            prod_ids = [p.id for p in mfg_products]
            
            # Find inspections for these products
            mfg_inspections = db.query(Inspection).join(Sample).join(Lot).filter(Lot.product_id.in_(prod_ids)).all()
            total_insps = len(mfg_inspections)
            
            if total_insps > 0:
                fails = len([i for i in mfg_inspections if i.overall_compliance == "NON_COMPLIANT"])
                m.compliance_rate = ((total_insps - fails) / total_insps) * 100.0
                
                # Check violations count
                violation_count = db.query(Violation).join(Inspection).join(Sample).join(Lot).filter(Lot.product_id.in_(prod_ids)).count()
                
                # Check repeat violations (same product failed more than once)
                product_fail_counts = {}
                for i in mfg_inspections:
                    if i.overall_compliance == "NON_COMPLIANT":
                        pid = i.sample.lot.product_id
                        product_fail_counts[pid] = product_fail_counts.get(pid, 0) + 1
                
                repeats = sum(1 for pid, count in product_fail_counts.items() if count > 1)
                
                # Packaging versions count
                pkg_versions = db.query(ProductVersion).filter(ProductVersion.product_id.in_(prod_ids)).count()
                
                # Calculate risk factors
                prev_violation_weight = min(30.0, violation_count * 3.0)
                repeat_violation_weight = min(25.0, repeats * 8.0)
                category_risk_weight = min(15.0, sum(p.category.base_risk_weight for p in mfg_products) / max(1, len(mfg_products)))
                packaging_change_weight = min(10.0, pkg_versions * 2.0)
                recent_failure_weight = 20.0 if any((datetime.datetime.utcnow() - i.timestamp).days < 30 and i.overall_compliance == "NON_COMPLIANT" for i in mfg_inspections) else 0.0
                
                risk_score_val = prev_violation_weight + repeat_violation_weight + category_risk_weight + packaging_change_weight + recent_failure_weight
                # Clamp to 0-100
                m.risk_score = min(100.0, max(0.0, risk_score_val))
                
                # Write risk score table entries
                r_score = RiskScore(target_type="MANUFACTURER", target_id=m.id, score=m.risk_score)
                db.add(r_score)
                db.flush()
                
                # Add factors
                factors = [
                    RiskFactor(risk_score_id=r_score.id, factor_name="Previous Violations Weight", weight=3.0, value=float(violation_count)),
                    RiskFactor(risk_score_id=r_score.id, factor_name="Repeat Violations Weight", weight=8.0, value=float(repeats)),
                    RiskFactor(risk_score_id=r_score.id, factor_name="Category Risk Weight", weight=1.0, value=category_risk_weight),
                    RiskFactor(risk_score_id=r_score.id, factor_name="Packaging Change Weight", weight=2.0, value=float(pkg_versions)),
                    RiskFactor(risk_score_id=r_score.id, factor_name="Recent Failures Weight", weight=20.0, value=1.0 if recent_failure_weight > 0 else 0.0)
                ]
                db.add_all(factors)
                
                # Create System Recommendations
                priority = "LOW"
                action = "ROUTINE_MONITORING"
                if m.risk_score >= 80:
                    priority = "CRITICAL"
                    action = "PROSECUTE"
                elif m.risk_score >= 60:
                    priority = "HIGH"
                    action = "PRIORITY_SAMPLE"
                elif m.risk_score >= 40:
                    priority = "MEDIUM"
                    action = "ENHANCED_INSPECTION"
                    
                rec = Recommendation(target_type="MANUFACTURER", target_id=m.id, action=action, priority=priority)
                db.add(rec)
                
                # Create cases for high risk manufacturers
                if m.risk_score >= 65:
                    m.status = "UNDER_INVESTIGATION"
                    case = InvestigationCase(
                        case_number=f"CASE-2026-{m.id:04d}",
                        manufacturer_id=m.id,
                        product_id=random.choice(mfg_products).id,
                        status="INVESTIGATION" if m.risk_score >= 80 else "UNDER_REVIEW",
                        risk_level=priority,
                        notes=f"Active review for recurring metrology compliance failures. Risk Score: {m.risk_score:.1f}%."
                    )
                    db.add(case)
            else:
                m.risk_score = 10.0
                m.compliance_rate = 100.0

        db.commit()

        # Seed audit logs
        logs = [
            AuditLog(user_id=1, action="LOGIN", details="Operator console logged in successfully."),
            AuditLog(user_id=4, action="RULE_MODIFICATION", details="Default legal metrology Rules seeded and rule versions configured to version 1."),
            AuditLog(user_id=4, action="USER_MANAGEMENT", details="Created roles: CAPTURE_OPERATOR, VERIFICATION_OFFICER, SENIOR_ENFORCEMENT_OFFICER, ADMIN.")
        ]
        db.add_all(logs)
        db.commit()

        print("Database Seeding Completed Successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
