import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import DocumentArchetype
from app.services.categorizer import categorizer
from app.services.extractor import extractor_service
from app.db.database import init_db, get_system_stats

client = TestClient(app)

def test_healthz():
    response = client.get("/api/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_categorizer_archetypes():
    invoice_text = "INVOICE #INV-1001 Date: 2026-01-01 Bill to Acme Inc Amount Due: $5,000.00 Net 30"
    res1 = categorizer.categorize_text(invoice_text)
    assert res1.archetype == DocumentArchetype.INVOICE

    resume_text = "Jane Doe Curriculum Vitae Work Experience Senior Software Engineer Skills: Python, React, Docker University Degree"
    res2 = categorizer.categorize_text(resume_text)
    assert res2.archetype == DocumentArchetype.RESUME

    contract_text = "This Master Services Agreement is entered into between Alpha Corp and Beta Inc. Governing law is Delaware. In witness whereof."
    res3 = categorizer.categorize_text(contract_text)
    assert res3.archetype == DocumentArchetype.CONTRACT

    report_text = "Annual Performance Report Executive Summary Q4 Metrics Service Availability 99.9% Recommendations for infrastructure."
    res4 = categorizer.categorize_text(report_text)
    assert res4.archetype == DocumentArchetype.REPORT

    policy_text = "Enterprise Information Security Policy standard operating procedure compliance ISO 27001 encryption at rest audit logs."
    res5 = categorizer.categorize_text(policy_text)
    assert res5.archetype == DocumentArchetype.POLICY_DOCUMENT

def test_date_and_monetary_extraction():
    sample_text = "Contract executed on 2026-03-15 with total fee of $125,500.00 USD payable before 2026-06-30."
    dates = extractor_service.extract_dates(sample_text)
    assert len(dates) >= 1
    assert any("2026-03-15" in d.value for d in dates)

    monetary = extractor_service.extract_monetary(sample_text)
    assert len(monetary) >= 1
    assert any(m.amount == 125500.0 for m in monetary)

def test_stats_and_documents_endpoint():
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)

    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_documents" in stats
    assert "archetype_counts" in stats

def test_corpus_search():
    search_res = client.get("/api/search?q=")
    assert search_res.status_code == 200
    data = search_res.json()
    assert "results" in data
    assert "total" in data
