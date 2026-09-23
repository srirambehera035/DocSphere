from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class DocumentArchetype(str, Enum):
    INVOICE = "Invoice"
    RESUME = "Resume"
    CONTRACT = "Contract"
    REPORT = "Report"
    POLICY_DOCUMENT = "Policy Document"
    MEMO = "Memo"
    PURCHASE_ORDER = "Purchase Order"
    NDA = "Non-Disclosure Agreement"
    TERM_SHEET = "Term Sheet"
    LETTER = "Letter"
    SPECIFICATION = "Specification"
    MEETING_MINUTES = "Meeting Minutes"
    PROPOSAL = "Proposal"

class EntityDate(BaseModel):
    value: str
    context: str
    page: int = 1

class EntityMonetary(BaseModel):
    amount: float
    currency: str = "USD"
    context: str
    page: int = 1

class EntityParty(BaseModel):
    name: str
    role: str
    details: str | None = None
    page: int = 1

class EvidenceClause(BaseModel):
    text: str
    page: int = 1
    category: str | None = None
    confidence: float = 1.0

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0
    page: int = 1

class InvoiceData(BaseModel):
    invoice_number: str | None = None
    vendor_name: str | None = None
    vendor_address: str | None = None
    customer_name: str | None = None
    customer_address: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    line_items: list[InvoiceLineItem] = []
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    currency: str = "USD"
    payment_terms: str | None = None
    page_reference: int = 1

class PurchaseOrderData(BaseModel):
    po_number: str | None = None
    buyer_name: str | None = None
    supplier_name: str | None = None
    order_date: str | None = None
    delivery_date: str | None = None
    line_items: list[InvoiceLineItem] = []
    total_amount: float | None = None
    currency: str = "USD"
    payment_terms: str | None = None
    shipping_address: str | None = None

class EducationItem(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: str | None = None
    page: int = 1

class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str | None = None
    highlights: list[str] = []
    page: int = 1

class ResumeData(BaseModel):
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[str] = []
    education: list[EducationItem] = []
    experience: list[ExperienceItem] = []
    certifications: list[str] = []

class ContractData(BaseModel):
    contract_title: str | None = None
    contracting_parties: list[EntityParty] = []
    effective_date: str | None = None
    expiration_date: str | None = None
    governing_law: str | None = None
    core_obligations: list[EvidenceClause] = []
    liability_clauses: list[EvidenceClause] = []
    liability_cap: str | None = None
    termination_terms: list[EvidenceClause] = []
    total_contract_value: str | None = None

class NDAData(BaseModel):
    nda_title: str | None = None
    disclosing_party: str | None = None
    receiving_party: str | None = None
    effective_date: str | None = None
    expiration_date: str | None = None
    confidential_information_scope: str | None = None
    obligations: list[EvidenceClause] = []
    governing_law: str | None = None

class TermSheetData(BaseModel):
    term_sheet_title: str | None = None
    parties: list[EntityParty] = []
    transaction_type: str | None = None
    valuation: str | None = None
    investment_amount: str | None = None
    key_terms: list[EvidenceClause] = []
    closing_date: str | None = None

class MemoData(BaseModel):
    memo_title: str | None = None
    from_party: str | None = None
    to_party: str | None = None
    date: str | None = None
    subject: str | None = None
    key_points: list[EvidenceClause] = []

class LetterData(BaseModel):
    letter_title: str | None = None
    sender: str | None = None
    recipient: str | None = None
    date: str | None = None
    subject: str | None = None
    key_points: list[EvidenceClause] = []

class SpecificationData(BaseModel):
    spec_title: str | None = None
    version: str | None = None
    author: str | None = None
    date: str | None = None
    scope: str | None = None
    requirements: list[EvidenceClause] = []
    technical_constraints: list[EvidenceClause] = []

class MeetingMinutesData(BaseModel):
    meeting_title: str | None = None
    date: str | None = None
    location: str | None = None
    attendees: list[str] = []
    agenda_items: list[EvidenceClause] = []
    action_items: list[EvidenceClause] = []
    decisions: list[EvidenceClause] = []

class ProposalData(BaseModel):
    proposal_title: str | None = None
    submitted_by: str | None = None
    submitted_to: str | None = None
    date: str | None = None
    total_value: str | None = None
    scope_of_work: list[EvidenceClause] = []
    deliverables: list[EvidenceClause] = []
    timeline: str | None = None

class MetricItem(BaseModel):
    metric: str
    value: str
    unit: str | None = None
    page: int = 1

class ReportData(BaseModel):
    report_title: str | None = None
    author_or_organization: str | None = None
    reporting_period: str | None = None
    executive_highlights: list[EvidenceClause] = []
    key_metrics: list[MetricItem] = []
    primary_findings: list[EvidenceClause] = []
    recommendations: list[EvidenceClause] = []

class ComplianceRule(BaseModel):
    rule: str
    severity: str = "Standard"
    target: str | None = None
    page: int = 1

class PolicyDocumentData(BaseModel):
    policy_title: str | None = None
    policy_identifier: str | None = None
    effective_date: str | None = None
    scope: str | None = None
    regulatory_frameworks: list[str] = []
    core_compliance_rules: list[ComplianceRule] = []
    enforcement_penalties: list[EvidenceClause] = []
    review_cycle: str | None = None

class StructuredEntities(BaseModel):
    dates: list[EntityDate] = []
    monetary_amounts: list[EntityMonetary] = []
    parties: list[EntityParty] = []
    terms: list[EvidenceClause] = []

class DocumentIntelligence(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: int = 1
    upload_timestamp: str
    file_url: str
    archetype: DocumentArchetype
    archetype_confidence: float
    archetype_rationale: str
    executive_summary: str
    operational_summary_points: list[EvidenceClause] = []
    core_obligations: list[EvidenceClause] = []
    key_deliverables: list[EvidenceClause] = []
    liability_clauses: list[EvidenceClause] = []
    extracted_entities: StructuredEntities
    structured_data: dict[str, Any]
    critical_keywords: list[str] = []
    technical_tags: list[str] = []
    extracted_text_preview: str
    extracted_text_full: str
    processing_time_ms: float
    llm_provider_used: str

class DocumentSummaryItem(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: int = 1
    upload_timestamp: str
    file_url: str
    archetype: DocumentArchetype
    archetype_confidence: float
    executive_summary: str
    critical_keywords: list[str] = []
    processing_time_ms: float

class SearchQuery(BaseModel):
    query: str = ""
    archetype: DocumentArchetype | None = None
    tag: str | None = None
    limit: int = 50
    offset: int = 0

class SearchResultItem(BaseModel):
    id: str
    filename: str
    archetype: DocumentArchetype
    upload_timestamp: str
    snippet: str
    match_score: float = 1.0
    critical_keywords: list[str] = []
    executive_summary: str
    page_count: int = 1

class SearchResponse(BaseModel):
    total: int
    results: list[SearchResultItem]

class SystemStats(BaseModel):
    total_documents: int
    archetype_counts: dict[str, int]
    storage_size_bytes: int
    active_llm_engine: str
    uptime_status: str
