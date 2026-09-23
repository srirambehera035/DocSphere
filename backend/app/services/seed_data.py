import os
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.core.config import settings
from app.db.database import save_document, get_db_connection
from app.models.schemas import DocumentIntelligence, DocumentArchetype
from app.services.ingestion import ingestion_service
from app.services.categorizer import categorizer
from app.services.extractor import extractor_service

def generate_sample_invoice_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('InvTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0f172a'))
    normal_style = ParagraphStyle('InvNormal', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'))
    bold_style = ParagraphStyle('InvBold', parent=styles['Normal'], fontSize=9, leading=13, fontName='Helvetica-Bold')

    story.append(Paragraph("INVOICE", title_style))
    story.append(Paragraph("<b>Apex Cloud Solutions LLC</b><br/>100 Montgomery St, Suite 1400<br/>San Francisco, CA 94104<br/>billing@apexcloud.io", normal_style))
    story.append(Spacer(1, 15))

    meta_data = [
        [Paragraph("<b>Invoice Number:</b> INV-2026-8891", normal_style), Paragraph("<b>Invoice Date:</b> 2026-03-01", normal_style)],
        [Paragraph("<b>Payment Terms:</b> Net 30 Days", normal_style), Paragraph("<b>Due Date:</b> 2026-03-31", normal_style)],
        [Paragraph("<b>Bill To:</b><br/>Acme Global Enterprises Inc.<br/>742 Evergreen Terrace<br/>Springfield, OR 97477", normal_style),
         Paragraph("<b>Ship To:</b><br/>Acme Primary Datacenter<br/>Building 4, Data Suite 200<br/>Austin, TX 78701", normal_style)]
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    items_data = [
        [Paragraph("<b>Description</b>", bold_style), Paragraph("<b>Qty</b>", bold_style), Paragraph("<b>Unit Price</b>", bold_style), Paragraph("<b>Total</b>", bold_style)],
        [Paragraph("Dedicated Cloud Kubernetes Cluster (c6i.8xlarge, 32 Nodes)", normal_style), Paragraph("1", normal_style), Paragraph("$4,200.00", normal_style), Paragraph("$4,200.00", normal_style)],
        [Paragraph("Distributed Managed PostgreSQL Storage (10TB SSD NVMe)", normal_style), Paragraph("1", normal_style), Paragraph("$1,850.00", normal_style), Paragraph("$1,850.00", normal_style)],
        [Paragraph("Enterprise Global CDN & Edge Cache Egress (50 TB)", normal_style), Paragraph("50", normal_style), Paragraph("$40.00", normal_style), Paragraph("$2,000.00", normal_style)],
        [Paragraph("24/7 Dedicated SRE Enterprise Support & SLA Tier 1", normal_style), Paragraph("1", normal_style), Paragraph("$1,500.00", normal_style), Paragraph("$1,500.00", normal_style)],
    ]
    t_items = Table(items_data, colWidths=[310, 50, 90, 90])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 12))

    summary_data = [
        [Paragraph("", normal_style), Paragraph("<b>Subtotal:</b>", normal_style), Paragraph("$9,550.00", normal_style)],
        [Paragraph("", normal_style), Paragraph("<b>Sales Tax (8.25%):</b>", normal_style), Paragraph("$787.88", normal_style)],
        [Paragraph("", normal_style), Paragraph("<b>Total Amount Due:</b>", bold_style), Paragraph("<b>$10,337.88</b>", bold_style)]
    ]
    t_summary = Table(summary_data, colWidths=[310, 140, 90])
    t_summary.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Remittance Instructions:</b> Direct wire transfer to Apex Cloud Solutions LLC, Routing #021000021, Account #884920192. Reference INV-2026-8891.", normal_style))
    doc.build(story)

def generate_sample_contract_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('ContTitle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#0f172a'))
    body_style = ParagraphStyle('ContBody', parent=styles['Normal'], fontSize=9, leading=14, textColor=colors.HexColor('#1e293b'))
    section_style = ParagraphStyle('ContSec', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#0f172a'), spaceBefore=8, spaceAfter=4)

    story.append(Paragraph("MASTER SERVICES AGREEMENT", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This Master Services Agreement is entered into on this 15th day of January, 2026 (the Effective Date), between <b>AlphaTech Enterprise Solutions Inc.</b>, a Delaware corporation having its principal office at 500 Technology Way, Seattle, WA 98101 (Provider), and <b>Global Dynamics Logistics Corp.</b>, having its principal office at 1200 Commerce Blvd, Chicago, IL 60601 (Customer).", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Scope of Services & Key Deliverables", section_style))
    story.append(Paragraph("Provider shall supply enterprise-grade AI automated document extraction, multi-tenant cloud data pipelines, and full-text search indexing as outlined in Statement of Work #1. Provider warrants 99.9% service availability excluding scheduled maintenance windows.", body_style))

    story.append(Paragraph("2. Financial Terms & Total Contract Value", section_style))
    story.append(Paragraph("Customer shall pay Provider an annualized recurring subscription fee of $240,000.00 USD payable quarterly in advance. Invoices are subject to Net 30 payment terms from the date of invoice presentation.", body_style))

    story.append(Paragraph("3. Confidentiality & Intellectual Property", section_style))
    story.append(Paragraph("Each party agrees that all confidential, proprietary, or business data disclosed during the term shall be held in strict confidence. Customer retains sole and exclusive ownership of all uploaded datasets and extracted document intelligence.", body_style))

    story.append(Paragraph("4. Limitation of Liability & Indemnification", section_style))
    story.append(Paragraph("Except for gross negligence or willful misconduct, neither party shall be liable for indirect, incidental, special, or consequential damages. Aggregate liability of either party arising out of or related to this agreement shall not exceed the total fees paid by Customer in the preceding twelve (12) months, or $250,000.00 USD.", body_style))

    story.append(Paragraph("5. Term and Termination", section_style))
    story.append(Paragraph("This Agreement commences on the Effective Date and continues for an initial term of two (2) years expiring on January 15, 2028. Either party may terminate for convenience with sixty (60) days prior written notice.", body_style))

    story.append(Paragraph("6. Governing Law & Jurisdiction", section_style))
    story.append(Paragraph("This Agreement shall be governed by and construed in accordance with the substantive laws of the State of Delaware, without regard to conflicts of law principles.", body_style))
    story.append(Spacer(1, 15))

    sig_data = [
        [Paragraph("<b>ALPHA TECH SOLUTIONS INC.</b><br/><br/>By: <i>Eleanor Vance</i><br/>Title: Chief Technology Officer<br/>Date: January 15, 2026", body_style),
         Paragraph("<b>GLOBAL DYNAMICS LOGISTICS CORP.</b><br/><br/>By: <i>Marcus Sterling</i><br/>Title: VP of Procurement<br/>Date: January 15, 2026", body_style)]
    ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    story.append(t_sig)
    doc.build(story)

def generate_sample_resume_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    name_style = ParagraphStyle('ResName', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#0f172a'))
    contact_style = ParagraphStyle('ResContact', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'))
    sec_style = ParagraphStyle('ResSec', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#0284c7'), spaceBefore=8, spaceAfter=2)
    body_style = ParagraphStyle('ResBody', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#1e293b'))

    story.append(Paragraph("SARAH CHEN", name_style))
    story.append(Paragraph("San Francisco, CA | (415) 555-0198 | sarah.chen.dev@gmail.com | linkedin.com/in/sarahchendev | github.com/schen", contact_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("PROFESSIONAL SUMMARY", sec_style))
    story.append(Paragraph("Staff Software Engineer with 8+ years of expertise in distributed cloud architectures, large-scale asynchronous document processing pipelines, and production machine learning serving. Track record of designing fault-tolerant backend systems serving over 10M daily active users.", body_style))

    story.append(Paragraph("TECHNICAL COMPETENCIES", sec_style))
    story.append(Paragraph("<b>Languages:</b> Python, TypeScript, Go, SQL, Rust, C++<br/><b>Frameworks & Tools:</b> FastAPI, React, Next.js, Node.js, PyTorch, LangChain, Celery, Docker, Kubernetes, Terraform<br/><b>Databases & Cloud:</b> PostgreSQL, Redis, SQLite FTS5, AWS (ECS, S3, RDS), Google Cloud Platform", body_style))

    story.append(Paragraph("PROFESSIONAL EXPERIENCE", sec_style))
    story.append(Paragraph("<b>Staff Distributed Systems Engineer</b> | Meridian Cloud Labs, San Francisco, CA | 2022 - Present", body_style))
    story.append(Paragraph("• Architected multi-tenant document ingestion pipeline handling 50,000 PDF/DOCX files per hour with p99 latency < 350ms.<br/>• Reduced cloud infrastructure compute expenditure by 34% through memory-efficient streaming parsers.<br/>• Mentored 12 mid-level and junior engineers across backend and infrastructure guilds.", body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Senior Backend Engineer</b> | DataScale Networks, San Jose, CA | 2019 - 2022", body_style))
    story.append(Paragraph("• Built high-throughput search microservice utilizing SQLite and Elasticsearch powering sub-50ms full-text document retrieval.<br/>• Spearheaded migration from legacy monolithic framework to containerized Kubernetes microservices on AWS.", body_style))

    story.append(Paragraph("EDUCATION & CERTIFICATIONS", sec_style))
    story.append(Paragraph("<b>University of California, Berkeley</b> — Bachelor of Science in Computer Science (2015 - 2019)<br/><b>Certifications:</b> AWS Certified Solutions Architect Professional, Certified Kubernetes Administrator (CKA)", body_style))
    doc.build(story)

def generate_sample_report_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('RepTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f172a'))
    meta_style = ParagraphStyle('RepMeta', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#64748b'))
    sec_style = ParagraphStyle('RepSec', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#047857'), spaceBefore=8, spaceAfter=3)
    body_style = ParagraphStyle('RepBody', parent=styles['Normal'], fontSize=8.5, leading=12.5, textColor=colors.HexColor('#1e293b'))

    story.append(Paragraph("Q1 2026 ENTERPRISE SYSTEM OPERATIONAL REPORT", title_style))
    story.append(Paragraph("<b>Author:</b> Cloud Operations & Engineering Governance Directorate | <b>Date:</b> March 31, 2026 | <b>Period:</b> Q1 2026", meta_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("EXECUTIVE HIGHLIGHTS", sec_style))
    story.append(Paragraph("During Q1 2026, the enterprise platform processed 4.82 million documents with zero data-loss incidents. Overall infrastructure availability reached 99.982%, surpassing our contractual SLA obligation of 99.9%. End-to-end entity extraction accuracy rose to 98.6% following deployment of enhanced structured schemas.", body_style))

    story.append(Paragraph("KEY OPERATIONAL METRICS", sec_style))
    metrics_data = [
        [Paragraph("<b>Metric Name</b>", body_style), Paragraph("<b>Q1 Target</b>", body_style), Paragraph("<b>Actual Result</b>", body_style), Paragraph("<b>Variance</b>", body_style)],
        [Paragraph("System Availability SLA", body_style), Paragraph("99.90%", body_style), Paragraph("99.98%", body_style), Paragraph("+0.08% (Exceeded)", body_style)],
        [Paragraph("Average Ingestion Latency", body_style), Paragraph("< 400 ms", body_style), Paragraph("285 ms", body_style), Paragraph("-115 ms (Optimal)", body_style)],
        [Paragraph("Total Documents Ingested", body_style), Paragraph("4,000,000", body_style), Paragraph("4,821,900", body_style), Paragraph("+20.5% (Growth)", body_style)],
        [Paragraph("FTS Search Query Response", body_style), Paragraph("< 100 ms", body_style), Paragraph("34 ms", body_style), Paragraph("-66 ms (Fast)", body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[170, 110, 110, 140])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ecfdf5')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#a7f3d0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_metrics)

    story.append(Paragraph("PRIMARY FINDINGS & RECOMMENDATIONS", sec_style))
    story.append(Paragraph("1. <b>Throughput Scaling:</b> Ingestion batch jobs hit peak concurrency between 13:00 - 16:00 UTC. Implementing pre-emptive autoscaling reduced processing queue depth by 62%.<br/>2. <b>Recommendations for Q2:</b> Commission secondary failover cluster in EU-West region and expand automated OCR fallback caching to optimize memory usage.", body_style))
    doc.build(story)

def generate_sample_policy_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('PolTitle', parent=styles['Heading1'], fontSize=15, leading=19, textColor=colors.HexColor('#0f172a'))
    meta_style = ParagraphStyle('PolMeta', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#64748b'))
    sec_style = ParagraphStyle('PolSec', parent=styles['Heading2'], fontSize=10.5, leading=14, textColor=colors.HexColor('#b91c1c'), spaceBefore=8, spaceAfter=3)
    body_style = ParagraphStyle('PolBody', parent=styles['Normal'], fontSize=8.5, leading=12.5, textColor=colors.HexColor('#1e293b'))

    story.append(Paragraph("ENTERPRISE INFORMATION SECURITY & COMPLIANCE POLICY", title_style))
    story.append(Paragraph("<b>Policy ID:</b> POL-SEC-2026-v4.2 | <b>Effective Date:</b> 2026-02-01 | <b>Classification:</b> Confidential Internal", meta_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Scope and Regulatory Applicability", sec_style))
    story.append(Paragraph("This standard governs all production information systems, cloud tenancies, employee workstations, and third-party data handlers. It implements compliance mandates aligned with <b>ISO/IEC 27001</b>, <b>SOC 2 Type II</b>, <b>GDPR</b>, and <b>NIST CSF v2.0</b>.", body_style))

    story.append(Paragraph("2. Mandatory Cryptographic and Access Controls", sec_style))
    story.append(Paragraph("• <b>Encryption at Rest:</b> All databases, object storage buckets, and document repositories must utilize AES-256 encryption with managed HSM key rotation every 90 days.<br/>• <b>Encryption in Transit:</b> TLS 1.3 is strictly enforced on all public and internal service mesh endpoints with cipher suites offering perfect forward secrecy.<br/>• <b>Multi-Factor Authentication:</b> FIDO2/WebAuthn hardware tokens are mandatory for all administrative access.", body_style))

    story.append(Paragraph("3. Data Retention and Audit Logging", sec_style))
    story.append(Paragraph("Immutable security audit logs must be retained for a statutory minimum of 365 days. Access logs must record timestamp, user identifier, IP address, and requested action.", body_style))

    story.append(Paragraph("4. Incident Response & Non-Compliance Penalties", sec_style))
    story.append(Paragraph("Suspected data disclosures or security anomalies must be reported to the Security Operations Center (soc@enterprise.internal) within 60 minutes. Failure to comply with security standards constitutes gross negligence and may result in immediate termination of employment or commercial contract termination.", body_style))
    doc.build(story)

async def seed_sample_documents(overwrite: bool = False) -> list[DocumentIntelligence]:
    samples_dir = Path("D:/ADP/samples")
    samples_dir.mkdir(parents=True, exist_ok=True)

    sample_specs = [
        ("sample_cloud_invoice.pdf", generate_sample_invoice_pdf),
        ("sample_master_services_agreement.pdf", generate_sample_contract_pdf),
        ("sample_software_engineer_resume.pdf", generate_sample_resume_pdf),
        ("sample_quarterly_operations_report.pdf", generate_sample_report_pdf),
        ("sample_infosec_compliance_policy.pdf", generate_sample_policy_pdf),
    ]

    seeded_docs: list[DocumentIntelligence] = []

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0 and not overwrite:
        return seeded_docs

    for filename, generator_func in sample_specs:
        file_path = samples_dir / filename
        generator_func(file_path)
        file_bytes = file_path.read_bytes()

        t0 = time.perf_counter()
        raw_text, pages_text, total_pages = ingestion_service.extract(filename, file_bytes)
        cat_result = categorizer.categorize_text(raw_text, filename)

        (
            struct_data,
            entities,
            summary,
            operational,
            obligations,
            deliverables,
            liabilities,
            keywords,
            tags,
            provider
        ) = await extractor_service.extract_all(raw_text, cat_result.archetype)

        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        doc_id = str(uuid.uuid4())

        upload_dest = settings.UPLOAD_DIR / f"{doc_id}_{filename}"
        upload_dest.write_bytes(file_bytes)

        doc_obj = DocumentIntelligence(
            id=doc_id,
            filename=filename,
            file_type="application/pdf",
            file_size_bytes=len(file_bytes),
            page_count=total_pages,
            upload_timestamp=datetime.now(timezone.utc).isoformat(),
            file_url=f"/api/documents/{doc_id}/file",
            archetype=cat_result.archetype,
            archetype_confidence=cat_result.confidence,
            archetype_rationale=cat_result.rationale,
            executive_summary=summary,
            operational_summary_points=operational,
            core_obligations=obligations,
            key_deliverables=deliverables,
            liability_clauses=liabilities,
            extracted_entities=entities,
            structured_data=struct_data,
            critical_keywords=keywords,
            technical_tags=tags,
            extracted_text_preview=raw_text[:500],
            extracted_text_full=raw_text,
            processing_time_ms=duration_ms,
            llm_provider_used=provider
        )

        save_document(doc_obj, str(upload_dest))
        seeded_docs.append(doc_obj)

    return seeded_docs
