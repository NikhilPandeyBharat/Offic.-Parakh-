import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from sqlalchemy.orm import Session
from backend.models import Inspection, ExtractedFact, ComplianceEvaluation, Violation

def generate_inspection_report(db: Session, inspection_id: int, output_path: str):
    """
    Generates a professional PDF report for the given inspection ID.
    """
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise ValueError(f"Inspection with ID {inspection_id} not found")

    # Fetch related info
    sample = insp.sample
    lot = sample.lot
    prod = lot.product
    mfg = prod.manufacturer
    officer_name = insp.officer.full_name if insp.officer else "N/A"

    facts = db.query(ExtractedFact).filter(ExtractedFact.inspection_id == inspection_id).all()
    evals = db.query(ComplianceEvaluation).filter(ComplianceEvaluation.inspection_id == inspection_id).all()
    violations = db.query(Violation).filter(Violation.inspection_id == inspection_id).all()

    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []

    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),  # Navy Blue
        spaceAfter=15,
        alignment=1  # Centered
    )
    
    subtitle_style = ParagraphStyle(
        name="SubTitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#718096"),
        alignment=1,
        spaceAfter=20
    )

    section_heading = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#2C5282"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        name="BodyTextCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#2D3748")
    )

    bold_body_style = ParagraphStyle(
        name="BoldBodyTextCustom",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    # Document Header
    story.append(Paragraph("PARAKH LEGAL METROLOGY PLATFORM", title_style))
    story.append(Paragraph("Official Legal Metrology Inspection and Compliance Report (DEMO DATA)", subtitle_style))
    story.append(Spacer(1, 10))

    # Inspection Metadata
    metadata_data = [
        [
            Paragraph("<b>Inspection ID:</b>", body_style),
            Paragraph(f"INSP-{insp.id:06d}", body_style),
            Paragraph("<b>Date/Time:</b>", body_style),
            Paragraph(insp.timestamp.strftime("%Y-%m-%d %H:%M:%S"), body_style)
        ],
        [
            Paragraph("<b>Product Name:</b>", body_style),
            Paragraph(prod.name, body_style),
            Paragraph("<b>Barcode:</b>", body_style),
            Paragraph(prod.barcode, body_style)
        ],
        [
            Paragraph("<b>Manufacturer:</b>", body_style),
            Paragraph(mfg.name, body_style),
            Paragraph("<b>Category:</b>", body_style),
            Paragraph(prod.category.name, body_style)
        ],
        [
            Paragraph("<b>Inspector:</b>", body_style),
            Paragraph(officer_name, body_style),
            Paragraph("<b>Overall Compliance:</b>", body_style),
            Paragraph(f"<b>{insp.overall_compliance}</b>", ParagraphStyle(
                name="ComplianceText",
                parent=body_style,
                textColor=colors.HexColor("#C53030") if insp.overall_compliance == "NON_COMPLIANT" else colors.HexColor("#2F855A") if insp.overall_compliance == "COMPLIANT" else colors.HexColor("#D69E2E")
            ))
        ]
    ]

    meta_table = Table(metadata_data, colWidths=[110, 160, 110, 160])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F7FAFC")),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Extracted Statutory Declarations
    story.append(Paragraph("1. Extracted Facts & Declarations", section_heading))
    facts_headers = [
        Paragraph("<b>Statutory Field</b>", bold_body_style),
        Paragraph("<b>Raw Observed Value</b>", bold_body_style),
        Paragraph("<b>Normalized Value</b>", bold_body_style),
        Paragraph("<b>Scan Confidence</b>", bold_body_style)
    ]
    facts_data = [facts_headers]
    for fact in facts:
        facts_data.append([
            Paragraph(fact.field_name.replace("_", " ").title(), body_style),
            Paragraph(fact.extracted_value or "None", body_style),
            Paragraph(fact.normalized_value or "None", body_style),
            Paragraph(f"{fact.confidence:.1f}%", body_style)
        ])
    
    facts_table = Table(facts_data, colWidths=[130, 200, 130, 80])
    facts_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor("#2C5282")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
    ]))
    story.append(facts_table)
    story.append(Spacer(1, 15))

    # Compliance Checklist Matrix
    story.append(Paragraph("2. Applicable Metrology Requirements Matrix", section_heading))
    eval_headers = [
        Paragraph("<b>Rule Reference</b>", bold_body_style),
        Paragraph("<b>Requirement Description</b>", bold_body_style),
        Paragraph("<b>Severity</b>", bold_body_style),
        Paragraph("<b>Evaluation</b>", bold_body_style)
    ]
    eval_data = [eval_headers]
    for ev in evals:
        rule_ver = ev.rule_version
        rule = rule_ver.rule
        
        status_color = "#2F855A" # Green
        if ev.status == "NON_COMPLIANT":
            status_color = "#C53030" # Red
        elif ev.status == "REQUIRES_VERIFICATION":
            status_color = "#D69E2E" # Yellow

        eval_data.append([
            Paragraph(rule.rule_code, body_style),
            Paragraph(rule.title, body_style),
            Paragraph(rule.severity, body_style),
            Paragraph(f"<b>{ev.status}</b>", ParagraphStyle(
                name=f"StatusCol_{ev.id}",
                parent=body_style,
                textColor=colors.HexColor(status_color)
            ))
        ])

    eval_table = Table(eval_data, colWidths=[100, 240, 100, 100])
    eval_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor("#2C5282")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
    ]))
    story.append(eval_table)
    story.append(Spacer(1, 15))

    # Violations Details (if any)
    if violations:
        story.append(Paragraph("3. Detected Rule Violations Details", section_heading))
        viol_headers = [
            Paragraph("<b>Rule</b>", bold_body_style),
            Paragraph("<b>Severity</b>", bold_body_style),
            Paragraph("<b>Description of Finding</b>", bold_body_style)
        ]
        viol_data = [viol_headers]
        for v in violations:
            rule_ver = v.rule_version
            rule = rule_ver.rule
            viol_data.append([
                Paragraph(rule.rule_code, body_style),
                Paragraph(v.severity, body_style),
                Paragraph(v.description, body_style)
            ])
        
        viol_table = Table(viol_data, colWidths=[100, 100, 340])
        viol_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor("#E53E3E")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FEB2B2")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FFF5F5")),
        ]))
        story.append(viol_table)
        story.append(Spacer(1, 15))

    # Authority Signature Area
    story.append(Spacer(1, 20))
    signature_data = [
        [
            Paragraph("<b>Prepared By:</b>", body_style),
            Paragraph("<b>Verified By:</b>", body_style)
        ],
        [
            Paragraph(f"<br/><br/>_______________________<br/>{officer_name}<br/>(Inspection Officer)", body_style),
            Paragraph("<br/><br/>_______________________<br/>Authorized Signatory<br/>(Verification Authority)", body_style)
        ]
    ]
    sig_table = Table(signature_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ]))
    story.append(sig_table)

    # Build the document
    doc.build(story)
