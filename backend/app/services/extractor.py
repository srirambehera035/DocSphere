import json
import re
import httpx
from typing import Any
from app.core.config import settings
from app.models.schemas import (
    DocumentArchetype,
    StructuredEntities,
    EntityDate,
    EntityMonetary,
    EntityParty,
    EvidenceClause,
    InvoiceData,
    InvoiceLineItem,
    PurchaseOrderData,
    ResumeData,
    EducationItem,
    ExperienceItem,
    ContractData,
    NDAData,
    TermSheetData,
    MemoData,
    LetterData,
    SpecificationData,
    MeetingMinutesData,
    ProposalData,
    ReportData,
    MetricItem,
    PolicyDocumentData,
    ComplianceRule
)

class ExtractionPipeline:
    DATE_PATTERNS = [
        r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b",
        r"\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]

    MONEY_PATTERNS = [
        r"(?:[\$\u20ac\xa3\u20b9]|USD|EUR|GBP|INR)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
        r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:USD|EUR|GBP|dollars|euros)"
    ]

    def parse_page_sections(self, text: str) -> list[tuple[int, list[str]]]:
        sections: list[tuple[int, list[str]]] = []
        current_page = 1
        current_lines: list[str] = []

        for line in text.split("\n"):
            m = re.match(r"^\[PAGE\s+(\d+)\]$", line.strip(), re.IGNORECASE)
            if m:
                if current_lines:
                    sections.append((current_page, current_lines))
                    current_lines = []
                current_page = int(m.group(1))
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_page, current_lines))

        return sections if sections else [(1, text.split("\n"))]

    def extract_dates(self, text: str) -> list[EntityDate]:
        results: list[EntityDate] = []
        seen = set()
        sections = self.parse_page_sections(text)

        for p_no, lines in sections:
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith("[PAGE"):
                    continue
                for pattern in self.DATE_PATTERNS:
                    for match in re.finditer(pattern, line_str, re.IGNORECASE):
                        val = match.group(0)
                        if val not in seen:
                            seen.add(val)
                            results.append(EntityDate(value=val, context=line_str[:120], page=p_no))
        return results[:12]

    def extract_monetary(self, text: str) -> list[EntityMonetary]:
        results: list[EntityMonetary] = []
        seen = set()
        sections = self.parse_page_sections(text)

        for p_no, lines in sections:
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith("[PAGE"):
                    continue
                for pattern in self.MONEY_PATTERNS:
                    for match in re.finditer(pattern, line_str, re.IGNORECASE):
                        val_str = match.group(1).replace(",", "")
                        try:
                            amt = float(val_str)
                            if amt not in seen:
                                seen.add(amt)
                                curr = "USD"
                                if "\u20ac" in line_str or "EUR" in line_str:
                                    curr = "EUR"
                                elif "\xa3" in line_str or "GBP" in line_str:
                                    curr = "GBP"
                                elif "\u20b9" in line_str or "INR" in line_str:
                                    curr = "INR"
                                results.append(EntityMonetary(amount=amt, currency=curr, context=line_str[:120], page=p_no))
                        except ValueError:
                            continue
        return results[:12]

    def extract_keywords_and_tags(self, text: str, archetype: DocumentArchetype) -> tuple[list[str], list[str]]:
        stop_words = {
            "the", "and", "for", "with", "this", "that", "from", "have", "will", "shall", "under", "which",
            "been", "were", "they", "their", "such", "other", "about", "into", "more", "also", "each", "page"
        }
        words = re.findall(r"\b[A-Za-z]{4,}\b", text)
        freq: dict[str, int] = {}
        for w in words:
            lw = w.lower()
            if lw not in stop_words:
                freq[lw] = freq.get(lw, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [k.capitalize() for k, _ in sorted_words[:12]]

        tags = [archetype.value]
        text_lower = text.lower()
        if "confidential" in text_lower:
            tags.append("Confidential")
        if "security" in text_lower or "iso" in text_lower or "audit" in text_lower:
            tags.append("Security")
        if "sla" in text_lower or "availability" in text_lower:
            tags.append("SLA")
        if "payment" in text_lower or "subtotal" in text_lower or "invoice" in text_lower:
            tags.append("Financial")
        if "gdpr" in text_lower or "compliance" in text_lower or "regulatory" in text_lower:
            tags.append("Compliance")
        if "python" in text_lower or "docker" in text_lower or "aws" in text_lower or "api" in text_lower:
            tags.append("Technical")
        if "governing law" in text_lower or "liability" in text_lower or "agreement" in text_lower:
            tags.append("Legal")

        return keywords, list(dict.fromkeys(tags))

    def deterministic_extract_invoice(self, text: str) -> InvoiceData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        inv_no = None
        vendor = None
        customer = None
        inv_date = None
        due_date = None
        total_amt = None
        subtotal = None
        tax = None
        payment_terms = None

        for l in lines:
            if not inv_no:
                m = re.search(r"(?:invoice\s*(?:number|no|#)|inv\s*#)\s*[:]?\s*([A-Z0-9-]+)", l, re.IGNORECASE)
                if m:
                    inv_no = m.group(1)
            if not inv_date:
                m = re.search(r"(?:invoice\s*date|date)\s*[:]?\s*(\S+.*)", l, re.IGNORECASE)
                if m:
                    inv_date = m.group(1).split(" ")[0].strip(",")
            if not due_date:
                m = re.search(r"(?:due\s*date|payment\s*due)\s*[:]?\s*(\S+.*)", l, re.IGNORECASE)
                if m:
                    due_date = m.group(1).split(" ")[0].strip(",")
            if not total_amt:
                m = re.search(r"(?:total|amount\s*due|balance\s*due)\s*[:]?\s*[\$\u20ac\xa3]?\s*([0-9,]+\.[0-9]{2})", l, re.IGNORECASE)
                if m:
                    try:
                        total_amt = float(m.group(1).replace(",", ""))
                    except ValueError:
                        pass
            if not subtotal:
                m = re.search(r"subtotal\s*[:]?\s*[\$\u20ac\xa3]?\s*([0-9,]+\.[0-9]{2})", l, re.IGNORECASE)
                if m:
                    try:
                        subtotal = float(m.group(1).replace(",", ""))
                    except ValueError:
                        pass
            if not tax:
                m = re.search(r"(?:tax|vat|gst)\s*(?:\([^\)]+\))?\s*[:]?\s*[\$\u20ac\xa3]?\s*([0-9,]+\.[0-9]{2})", l, re.IGNORECASE)
                if m:
                    try:
                        tax = float(m.group(1).replace(",", ""))
                    except ValueError:
                        pass
            if not payment_terms:
                m = re.search(r"(?:net\s*\d+|due\s*on\s*receipt|payment\s*terms\s*[:]?\s*[^\n]+)", l, re.IGNORECASE)
                if m:
                    payment_terms = m.group(0)

        for i, l in enumerate(lines[:12]):
            if re.search(r"bill\s*to|client", l, re.IGNORECASE):
                if i + 1 < len(lines):
                    customer = lines[i + 1]
            if not vendor and i < 4 and not re.search(r"invoice|page|date", l, re.IGNORECASE):
                vendor = l

        line_items: list[InvoiceLineItem] = []
        for l in lines:
            m = re.search(r"([A-Za-z0-9\s-]{4,})\s+(\d+)\s+[\$\u20ac\xa3]?([0-9,]+\.[0-9]{2})\s+[\$\u20ac\xa3]?([0-9,]+\.[0-9]{2})", l)
            if m:
                desc = m.group(1).strip()
                if desc.lower() not in {"total", "subtotal", "tax", "balance"}:
                    line_items.append(
                        InvoiceLineItem(
                            description=desc,
                            quantity=float(m.group(2)),
                            unit_price=float(m.group(3).replace(",", "")),
                            total=float(m.group(4).replace(",", "")),
                            page=1
                        )
                    )

        return InvoiceData(
            invoice_number=inv_no,
            vendor_name=vendor,
            customer_name=customer,
            invoice_date=inv_date,
            due_date=due_date,
            line_items=line_items,
            subtotal=subtotal,
            tax_amount=tax,
            total_amount=total_amt,
            payment_terms=payment_terms,
            page_reference=1
        )

    def deterministic_extract_purchase_order(self, text: str) -> PurchaseOrderData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        po_number = None
        buyer = None
        supplier = None
        order_date = None
        delivery_date = None
        total_amt = None
        payment_terms = None

        for l in lines:
            if not po_number:
                m = re.search(r"(?:purchase\s*order\s*(?:number|no|#)|po\s*(?:number|no|#))\s*[:]?\s*([A-Z0-9-]+)", l, re.IGNORECASE)
                if m:
                    po_number = m.group(1)
            if not order_date:
                m = re.search(r"(?:order\s*date|date)\s*[:]?\s*(\S+.*)", l, re.IGNORECASE)
                if m:
                    order_date = m.group(1).split(" ")[0].strip(",")
            if not delivery_date:
                m = re.search(r"(?:delivery\s*date|ship\s*date|required\s*by)\s*[:]?\s*(\S+.*)", l, re.IGNORECASE)
                if m:
                    delivery_date = m.group(1).split(" ")[0].strip(",")
            if not total_amt:
                m = re.search(r"(?:total|order\s*total|grand\s*total)\s*[:]?\s*[\$\u20ac\xa3]?\s*([0-9,]+\.[0-9]{2})", l, re.IGNORECASE)
                if m:
                    try:
                        total_amt = float(m.group(1).replace(",", ""))
                    except ValueError:
                        pass
            if not payment_terms:
                m = re.search(r"(?:net\s*\d+|payment\s*terms\s*[:]?\s*[^\n]+)", l, re.IGNORECASE)
                if m:
                    payment_terms = m.group(0)

        for i, l in enumerate(lines[:10]):
            if re.search(r"buyer|bill\s*to|ordered\s*by", l, re.IGNORECASE):
                if i + 1 < len(lines):
                    buyer = lines[i + 1]
            if re.search(r"supplier|vendor|sell\s*to", l, re.IGNORECASE):
                if i + 1 < len(lines):
                    supplier = lines[i + 1]

        return PurchaseOrderData(
            po_number=po_number,
            buyer_name=buyer,
            supplier_name=supplier,
            order_date=order_date,
            delivery_date=delivery_date,
            total_amount=total_amt,
            payment_terms=payment_terms
        )

    def deterministic_extract_contract(self, text: str) -> ContractData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        parties: list[EntityParty] = []
        text_norm = re.sub(r"\s+", " ", text)
        m_parties = re.search(r"between\s+([A-Z][A-Za-z0-9\s.&'-]+?)(?:,\s*[^\(]+?)?\s*\(([A-Za-z\s]+)\)[,\s]+and\s+([A-Z][A-Za-z0-9\s.&'-]+?)(?:,\s*[^\(]+?)?\s*\(([A-Za-z\s]+)\)", text_norm, re.IGNORECASE)
        if m_parties:
            p1_name = m_parties.group(1).strip().strip(",")
            p1_role = m_parties.group(2).strip()
            p2_name = m_parties.group(3).strip().strip(",")
            p2_role = m_parties.group(4).strip()
            parties.append(EntityParty(name=p1_name, role=p1_role, page=1))
            parties.append(EntityParty(name=p2_name, role=p2_role, page=1))

        if not parties:
            m_simple = re.search(r"between\s+([A-Z][A-Za-z0-9\s.&'-]{3,60}?)\s*,\s*.*?\s+and\s+([A-Z][A-Za-z0-9\s.&'-]{3,60}?)(?:,\s*|\.|\()", text_norm, re.IGNORECASE)
            if m_simple:
                parties.append(EntityParty(name=m_simple.group(1).strip().strip(","), role="Service Provider", page=1))
                parties.append(EntityParty(name=m_simple.group(2).strip().strip(","), role="Customer", page=1))

        effective_date = None
        m_date = re.search(r"(?:effective date|dated as of)\s*[:]?\s*([^\n.,]+)", text, re.IGNORECASE)
        if m_date:
            effective_date = m_date.group(1).strip()

        gov_law = None
        m_gov = re.search(r"governed by.*?laws of\s+([^,.\n]+)", text, re.IGNORECASE)
        if m_gov:
            gov_law = m_gov.group(1).strip()

        val_match = re.search(r"[\$\u20ac\xa3]\s*([0-9,]+(?:\.[0-9]{2})?)", text)
        total_val = val_match.group(0) if val_match else None

        obligations: list[EvidenceClause] = []
        liabilities: list[EvidenceClause] = []
        terminations: list[EvidenceClause] = []

        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:shall|warrants|agrees to|must provide)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 20 and len(obligations) < 4:
                        obligations.append(EvidenceClause(text=clean_l, page=p_no, category="Obligation"))
                if re.search(r"\b(?:liability|indemnif|damages|cap)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 20 and len(liabilities) < 3:
                        liabilities.append(EvidenceClause(text=clean_l, page=p_no, category="Liability"))
                if re.search(r"\b(?:terminate|termination|notice period)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 20 and len(terminations) < 3:
                        terminations.append(EvidenceClause(text=clean_l, page=p_no, category="Termination"))

        return ContractData(
            contract_title=title,
            contracting_parties=parties,
            effective_date=effective_date,
            expiration_date=None,
            governing_law=gov_law,
            core_obligations=obligations,
            liability_clauses=liabilities,
            liability_cap=liabilities[0].text if liabilities else None,
            termination_terms=terminations,
            total_contract_value=total_val
        )

    def deterministic_extract_nda(self, text: str) -> NDAData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        text_norm = re.sub(r"\s+", " ", text)

        disclosing = None
        receiving = None
        m_disc = re.search(r"disclosing\s*party\s*[:\"']?\s*([A-Z][A-Za-z0-9\s.&'-]{3,60}?)(?:\s*[,\.\(]|$)", text_norm, re.IGNORECASE)
        if m_disc:
            disclosing = m_disc.group(1).strip()
        m_recv = re.search(r"receiving\s*party\s*[:\"']?\s*([A-Z][A-Za-z0-9\s.&'-]{3,60}?)(?:\s*[,\.\(]|$)", text_norm, re.IGNORECASE)
        if m_recv:
            receiving = m_recv.group(1).strip()

        effective_date = None
        m_date = re.search(r"(?:effective date|dated)\s*[:]?\s*([^\n.,]+)", text, re.IGNORECASE)
        if m_date:
            effective_date = m_date.group(1).strip()

        gov_law = None
        m_gov = re.search(r"governed by.*?laws of\s+([^,.\n]+)", text, re.IGNORECASE)
        if m_gov:
            gov_law = m_gov.group(1).strip()

        obligations: list[EvidenceClause] = []
        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:shall not|must not|agrees not to|will not disclose)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 20 and len(obligations) < 4:
                        obligations.append(EvidenceClause(text=clean_l, page=p_no, category="Obligation"))

        return NDAData(
            nda_title=title,
            disclosing_party=disclosing,
            receiving_party=receiving,
            effective_date=effective_date,
            governing_law=gov_law,
            obligations=obligations
        )

    def deterministic_extract_term_sheet(self, text: str) -> TermSheetData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        text_norm = re.sub(r"\s+", " ", text)

        parties: list[EntityParty] = []
        m_parties = re.search(r"between\s+([A-Z][A-Za-z0-9\s.&'-]+?)\s+and\s+([A-Z][A-Za-z0-9\s.&'-]{3,60}?)(?:,|\.|$)", text_norm, re.IGNORECASE)
        if m_parties:
            parties.append(EntityParty(name=m_parties.group(1).strip(), role="Investor", page=1))
            parties.append(EntityParty(name=m_parties.group(2).strip(), role="Company", page=1))

        valuation = None
        m_val = re.search(r"(?:pre-money\s*valuation|post-money\s*valuation|valuation)\s*[:]?\s*([\$\u20ac\xa3]?[0-9,]+(?:\.[0-9]+)?\s*(?:million|billion|M|B)?)", text, re.IGNORECASE)
        if m_val:
            valuation = m_val.group(1).strip()

        investment = None
        m_inv = re.search(r"(?:investment\s*amount|total\s*investment|funding\s*amount)\s*[:]?\s*([\$\u20ac\xa3]?[0-9,]+(?:\.[0-9]+)?\s*(?:million|billion|M|B)?)", text, re.IGNORECASE)
        if m_inv:
            investment = m_inv.group(1).strip()

        key_terms: list[EvidenceClause] = []
        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:liquidation|anti-dilution|vesting|board seat|option pool|pro-rata)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 15 and len(key_terms) < 5:
                        key_terms.append(EvidenceClause(text=clean_l, page=p_no, category="Key Term"))

        return TermSheetData(
            term_sheet_title=title,
            parties=parties,
            valuation=valuation,
            investment_amount=investment,
            key_terms=key_terms
        )

    def deterministic_extract_resume(self, text: str) -> ResumeData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        candidate_name = lines[0] if lines else None
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = email_match.group(0) if email_match else None
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else None

        skill_keywords = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Docker", "Kubernetes",
            "AWS", "GCP", "SQL", "PostgreSQL", "MongoDB", "Git", "REST APIs", "FastAPI", "GraphQL",
            "CI/CD", "Terraform", "Java", "Go", "Rust", "C++", "PyTorch"
        ]
        skills = [s for s in skill_keywords if re.search(r"\b" + re.escape(s) + r"\b", text, re.IGNORECASE)]

        education: list[EducationItem] = []
        for l in lines:
            if re.search(r"(?:university|institute|college|bachelor|master|b\.s|m\.s|degree)", l, re.IGNORECASE):
                education.append(EducationItem(institution=l, page=1))
                if len(education) >= 2:
                    break

        experience: list[ExperienceItem] = []
        for i, l in enumerate(lines):
            if re.search(r"\b(?:engineer|developer|architect|lead|consultant|manager)\b", l, re.IGNORECASE):
                company = lines[i-1] if i > 0 and len(lines[i-1]) < 50 else None
                experience.append(ExperienceItem(company=company or "Organization", role=l, page=1))
                if len(experience) >= 3:
                    break

        return ResumeData(
            candidate_name=candidate_name,
            email=email,
            phone=phone,
            location=None,
            summary=lines[1] if len(lines) > 1 else None,
            skills=skills,
            education=education,
            experience=experience,
            certifications=[]
        )

    def deterministic_extract_report(self, text: str) -> ReportData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        highlights: list[EvidenceClause] = []
        metrics: list[MetricItem] = []
        findings: list[EvidenceClause] = []

        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:\d+%\s*|\d+\.\d+%\s*|\d+\s*ms)\b", clean_l):
                    metrics.append(MetricItem(metric="Metric Finding", value=clean_l[:60], page=p_no))
                elif re.search(r"\b(?:highlight|achieved|surpassed|increased|decreased)\b", clean_l, re.IGNORECASE):
                    highlights.append(EvidenceClause(text=clean_l, page=p_no, category="Highlight"))
                elif re.search(r"\b(?:finding|recommend|action|plan)\b", clean_l, re.IGNORECASE):
                    findings.append(EvidenceClause(text=clean_l, page=p_no, category="Finding"))

        return ReportData(
            report_title=title,
            author_or_organization=lines[1] if len(lines) > 1 else None,
            reporting_period=None,
            executive_highlights=highlights[:4],
            key_metrics=metrics[:6],
            primary_findings=findings[:4],
            recommendations=[]
        )

    def deterministic_extract_policy(self, text: str) -> PolicyDocumentData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        rules: list[ComplianceRule] = []
        penalties: list[EvidenceClause] = []

        effective_date = None
        m_date = re.search(r"(?:effective date|effective)\s*[:]?\s*([^\n.,]+)", text, re.IGNORECASE)
        if m_date:
            effective_date = m_date.group(1).strip()

        scope = None
        m_scope = re.search(r"(?:scope|applies to|applicable to)\s*[:]?\s*([^\n]+)", text, re.IGNORECASE)
        if m_scope:
            scope = m_scope.group(1).strip()

        frameworks: list[str] = []
        for fw in ["GDPR", "HIPAA", "ISO 27001", "SOC 2", "PCI DSS", "NIST"]:
            if fw.lower() in text.lower():
                frameworks.append(fw)

        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:must|mandatory|strictly enforced|required to)\b", clean_l, re.IGNORECASE):
                    rules.append(ComplianceRule(rule=clean_l, severity="High", page=p_no))
                elif re.search(r"\b(?:penalty|violation|disciplinary|termination)\b", clean_l, re.IGNORECASE):
                    penalties.append(EvidenceClause(text=clean_l, page=p_no, category="Penalty"))

        return PolicyDocumentData(
            policy_title=title,
            policy_identifier=None,
            effective_date=effective_date,
            scope=scope,
            regulatory_frameworks=frameworks,
            core_compliance_rules=rules[:5],
            enforcement_penalties=penalties[:3],
            review_cycle=None
        )

    def deterministic_extract_memo(self, text: str) -> MemoData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        from_party = None
        to_party = None
        date = None
        subject = None

        for l in lines:
            if not from_party:
                m = re.search(r"^from\s*[:]\s*(.+)$", l, re.IGNORECASE)
                if m:
                    from_party = m.group(1).strip()
            if not to_party:
                m = re.search(r"^to\s*[:]\s*(.+)$", l, re.IGNORECASE)
                if m:
                    to_party = m.group(1).strip()
            if not date:
                m = re.search(r"^date\s*[:]\s*(.+)$", l, re.IGNORECASE)
                if m:
                    date = m.group(1).strip()
            if not subject:
                m = re.search(r"^(?:subject|re|subj)\s*[:]\s*(.+)$", l, re.IGNORECASE)
                if m:
                    subject = m.group(1).strip()

        title = subject or (lines[0] if lines else None)

        key_points: list[EvidenceClause] = []
        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if len(clean_l) > 30 and re.search(r"\b(?:please|action|note|important|request|required|must)\b", clean_l, re.IGNORECASE):
                    if len(key_points) < 4:
                        key_points.append(EvidenceClause(text=clean_l, page=p_no, category="Key Point"))

        return MemoData(
            memo_title=title,
            from_party=from_party,
            to_party=to_party,
            date=date,
            subject=subject,
            key_points=key_points
        )

    def deterministic_extract_letter(self, text: str) -> LetterData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        recipient = None
        date = None
        subject = None

        for i, l in enumerate(lines[:10]):
            if not date:
                for pat in self.DATE_PATTERNS:
                    if re.search(pat, l, re.IGNORECASE):
                        date = l
                        break
            if not recipient:
                if re.search(r"^dear\b", l, re.IGNORECASE):
                    m = re.search(r"^dear\s+(.+?)(?:,|$)", l, re.IGNORECASE)
                    if m:
                        recipient = m.group(1).strip()
            if not subject:
                m = re.search(r"^(?:re|subject)\s*[:]\s*(.+)$", l, re.IGNORECASE)
                if m:
                    subject = m.group(1).strip()

        sender = None
        if lines and not re.search(r"\.", lines[-1]):
            sender = lines[-1]

        title = subject or (lines[0] if lines else None)

        key_points: list[EvidenceClause] = []
        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if len(clean_l) > 40 and len(key_points) < 3:
                    if not re.search(r"^dear|sincerely|regards", clean_l, re.IGNORECASE):
                        key_points.append(EvidenceClause(text=clean_l, page=p_no, category="Content"))

        return LetterData(
            letter_title=title,
            sender=sender,
            recipient=recipient,
            date=date,
            subject=subject,
            key_points=key_points
        )

    def deterministic_extract_specification(self, text: str) -> SpecificationData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        version = None
        m_ver = re.search(r"(?:version|ver|v)\s*[:]?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        if m_ver:
            version = m_ver.group(1)
        date = None
        m_date = re.search(r"(?:date|created|updated)\s*[:]?\s*([^\n.,]+)", text, re.IGNORECASE)
        if m_date:
            for pat in self.DATE_PATTERNS:
                dm = re.search(pat, m_date.group(1), re.IGNORECASE)
                if dm:
                    date = dm.group(0)
                    break

        requirements: list[EvidenceClause] = []
        constraints: list[EvidenceClause] = []
        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:shall|must|required|requirement)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 15 and len(requirements) < 5:
                        requirements.append(EvidenceClause(text=clean_l, page=p_no, category="Requirement"))
                elif re.search(r"\b(?:constraint|limit|maximum|minimum|not exceed)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 15 and len(constraints) < 3:
                        constraints.append(EvidenceClause(text=clean_l, page=p_no, category="Constraint"))

        return SpecificationData(
            spec_title=title,
            version=version,
            author=None,
            date=date,
            scope=None,
            requirements=requirements,
            technical_constraints=constraints
        )

    def deterministic_extract_meeting_minutes(self, text: str) -> MeetingMinutesData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None
        date = None
        for l in lines[:10]:
            for pat in self.DATE_PATTERNS:
                dm = re.search(pat, l, re.IGNORECASE)
                if dm:
                    date = dm.group(0)
                    break
            if date:
                break

        attendees: list[str] = []
        in_attendees = False
        for l in lines:
            if re.search(r"^attendees?\s*[:]?", l, re.IGNORECASE):
                in_attendees = True
                continue
            if in_attendees:
                if re.search(r"^(?:agenda|action|minutes|subject|date)", l, re.IGNORECASE):
                    in_attendees = False
                elif len(l) > 2 and len(l) < 60:
                    attendees.append(l)
                    if len(attendees) >= 10:
                        break

        action_items: list[EvidenceClause] = []
        decisions: list[EvidenceClause] = []
        agenda_items: list[EvidenceClause] = []

        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:action item|assigned to|owner|due by)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 10 and len(action_items) < 5:
                        action_items.append(EvidenceClause(text=clean_l, page=p_no, category="Action Item"))
                elif re.search(r"\b(?:decided|resolved|agreed|approved|rejected)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 10 and len(decisions) < 4:
                        decisions.append(EvidenceClause(text=clean_l, page=p_no, category="Decision"))
                elif re.search(r"^\d+\.\s+|^-\s+|^•\s+", clean_l):
                    if len(clean_l) > 10 and len(agenda_items) < 5:
                        agenda_items.append(EvidenceClause(text=clean_l, page=p_no, category="Agenda Item"))

        return MeetingMinutesData(
            meeting_title=title,
            date=date,
            attendees=attendees,
            agenda_items=agenda_items,
            action_items=action_items,
            decisions=decisions
        )

    def deterministic_extract_proposal(self, text: str) -> ProposalData:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[PAGE")]
        title = lines[0] if lines else None

        submitted_by = None
        submitted_to = None
        m_by = re.search(r"(?:submitted by|prepared by|from)\s*[:]?\s*([A-Z][A-Za-z0-9\s.&'-]{3,60}?)(?:\s*[,\.\n]|$)", text, re.IGNORECASE)
        if m_by:
            submitted_by = m_by.group(1).strip()
        m_to = re.search(r"(?:submitted to|prepared for|to)\s*[:]?\s*([A-Z][A-Za-z0-9\s.&'-]{3,60}?)(?:\s*[,\.\n]|$)", text, re.IGNORECASE)
        if m_to:
            submitted_to = m_to.group(1).strip()

        date = None
        m_date = re.search(r"(?:date|proposal date)\s*[:]?\s*([^\n.,]+)", text, re.IGNORECASE)
        if m_date:
            for pat in self.DATE_PATTERNS:
                dm = re.search(pat, m_date.group(1), re.IGNORECASE)
                if dm:
                    date = dm.group(0)
                    break

        total_value = None
        m_val = re.search(r"(?:total|budget|estimated cost|project cost)\s*[:]?\s*[\$\u20ac\xa3]?\s*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        if m_val:
            total_value = m_val.group(1)

        scope_items: list[EvidenceClause] = []
        deliverables: list[EvidenceClause] = []
        sections = self.parse_page_sections(text)
        for p_no, p_lines in sections:
            for l in p_lines:
                clean_l = l.strip()
                if not clean_l or clean_l.startswith("[PAGE"):
                    continue
                if re.search(r"\b(?:scope|will provide|we will|objective)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 15 and len(scope_items) < 4:
                        scope_items.append(EvidenceClause(text=clean_l, page=p_no, category="Scope"))
                elif re.search(r"\b(?:deliverable|milestone|output|deliverables)\b", clean_l, re.IGNORECASE):
                    if len(clean_l) > 15 and len(deliverables) < 4:
                        deliverables.append(EvidenceClause(text=clean_l, page=p_no, category="Deliverable"))

        return ProposalData(
            proposal_title=title,
            submitted_by=submitted_by,
            submitted_to=submitted_to,
            date=date,
            total_value=total_value,
            scope_of_work=scope_items,
            deliverables=deliverables
        )

    async def call_gemini_api(self, prompt: str, text: str) -> dict[str, Any] | None:
        if not settings.GEMINI_API_KEY:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"text": f"\n\nDOCUMENT TEXT WITH PAGE MARKERS:\n{text[:15000]}"}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        }
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_json = parts[0].get("text", "")
                            return json.loads(raw_json)
        except Exception:
            return None
        return None

    async def call_openai_api(self, prompt: str, text: str) -> dict[str, Any] | None:
        if not settings.OPENAI_API_KEY:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a document intelligence system. Output valid JSON only. Extract exact values from the document. Never invent or hallucinate data."},
                {"role": "user", "content": f"{prompt}\n\nDOCUMENT TEXT:\n{text[:15000]}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception:
            return None
        return None

    async def call_claude_api(self, prompt: str, text: str) -> dict[str, Any] | None:
        if not settings.ANTHROPIC_API_KEY:
            return None
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": f"{prompt}\n\nIMPORTANT: Respond with ONLY valid JSON. Never invent data.\n\nDOCUMENT TEXT:\n{text[:15000]}"
                }
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["content"][0]["text"]
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
        except Exception:
            return None
        return None

    async def call_ollama_api(self, prompt: str, text: str) -> dict[str, Any] | None:
        if not settings.OLLAMA_BASE_URL:
            return None
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "You are a document intelligence system. Output valid JSON only. Extract exact values from the document. Never invent data."},
                {"role": "user", "content": f"{prompt}\n\nDOCUMENT TEXT:\n{text[:12000]}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception:
            return None
        return None

    async def extract_all(self, text: str, archetype: DocumentArchetype) -> tuple[dict[str, Any], StructuredEntities, str, list[EvidenceClause], list[EvidenceClause], list[EvidenceClause], list[EvidenceClause], list[str], list[str], str]:
        dates = self.extract_dates(text)
        monetary = self.extract_monetary(text)
        keywords, tags = self.extract_keywords_and_tags(text, archetype)

        llm_data: dict[str, Any] | None = None
        provider_used = "Deterministic Engine"

        prompt = (
            f"Analyze the document text. The document is classified as {archetype.value}. "
            "Extract structured domain entities in JSON format: "
            "1. executive_summary (string: concise abstract based ONLY on document content) "
            "2. operational_summary_points (array of objects with {text, page, confidence}) "
            "3. core_obligations (array of objects with {text, page, category}) "
            "4. key_deliverables (array of objects with {text, page, category}) "
            "5. liability_clauses (array of objects with {text, page, category}) "
            "6. structured_data (archetype-specific fields; use null for missing fields, never invent values)"
        )

        if settings.GEMINI_API_KEY:
            llm_res = await self.call_gemini_api(prompt, text)
            if llm_res:
                llm_data = llm_res
                provider_used = "Gemini 2.5 Flash"
        if not llm_data and settings.OPENAI_API_KEY:
            llm_res = await self.call_openai_api(prompt, text)
            if llm_res:
                llm_data = llm_res
                provider_used = "OpenAI GPT-4o-mini"
        if not llm_data and settings.ANTHROPIC_API_KEY:
            llm_res = await self.call_claude_api(prompt, text)
            if llm_res:
                llm_data = llm_res
                provider_used = "Claude 3.5 Sonnet"
        if not llm_data and settings.OLLAMA_BASE_URL:
            llm_res = await self.call_ollama_api(prompt, text)
            if llm_res:
                llm_data = llm_res
                provider_used = f"Ollama ({settings.OLLAMA_MODEL})"

        structured_data: dict[str, Any]
        if archetype == DocumentArchetype.INVOICE:
            structured_data = self.deterministic_extract_invoice(text).model_dump()
        elif archetype == DocumentArchetype.PURCHASE_ORDER:
            structured_data = self.deterministic_extract_purchase_order(text).model_dump()
        elif archetype == DocumentArchetype.RESUME:
            structured_data = self.deterministic_extract_resume(text).model_dump()
        elif archetype == DocumentArchetype.CONTRACT:
            structured_data = self.deterministic_extract_contract(text).model_dump()
        elif archetype == DocumentArchetype.NDA:
            structured_data = self.deterministic_extract_nda(text).model_dump()
        elif archetype == DocumentArchetype.TERM_SHEET:
            structured_data = self.deterministic_extract_term_sheet(text).model_dump()
        elif archetype == DocumentArchetype.REPORT:
            structured_data = self.deterministic_extract_report(text).model_dump()
        elif archetype == DocumentArchetype.MEMO:
            structured_data = self.deterministic_extract_memo(text).model_dump()
        elif archetype == DocumentArchetype.LETTER:
            structured_data = self.deterministic_extract_letter(text).model_dump()
        elif archetype == DocumentArchetype.SPECIFICATION:
            structured_data = self.deterministic_extract_specification(text).model_dump()
        elif archetype == DocumentArchetype.MEETING_MINUTES:
            structured_data = self.deterministic_extract_meeting_minutes(text).model_dump()
        elif archetype == DocumentArchetype.PROPOSAL:
            structured_data = self.deterministic_extract_proposal(text).model_dump()
        else:
            structured_data = self.deterministic_extract_policy(text).model_dump()

        if llm_data and isinstance(llm_data.get("structured_data"), dict):
            for k, v in llm_data["structured_data"].items():
                if v is not None and v != "" and v != []:
                    structured_data[k] = v

        summary = f"{archetype.value} document."
        if archetype == DocumentArchetype.INVOICE:
            vendor = structured_data.get("vendor_name")
            customer = structured_data.get("customer_name")
            total = structured_data.get("total_amount")
            parts = ["Commercial invoice"]
            if vendor:
                parts.append(f"from {vendor}")
            if customer:
                parts.append(f"to {customer}")
            if total:
                parts.append(f"Total: {total}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.PURCHASE_ORDER:
            buyer = structured_data.get("buyer_name")
            supplier = structured_data.get("supplier_name")
            total = structured_data.get("total_amount")
            parts = ["Purchase order"]
            if buyer:
                parts.append(f"from {buyer}")
            if supplier:
                parts.append(f"to {supplier}")
            if total:
                parts.append(f"Total: {total}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.CONTRACT:
            title = structured_data.get("contract_title")
            parties_str = " & ".join(p.get("name", "") for p in structured_data.get("contracting_parties", []) if isinstance(p, dict) and p.get("name"))
            parts = [f"Legal contract ({title})" if title else "Legal contract"]
            if parties_str:
                parts.append(f"between {parties_str}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.NDA:
            disc = structured_data.get("disclosing_party")
            recv = structured_data.get("receiving_party")
            parts = ["Non-Disclosure Agreement"]
            if disc:
                parts.append(f"— Disclosing: {disc}")
            if recv:
                parts.append(f"Receiving: {recv}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.TERM_SHEET:
            title = structured_data.get("term_sheet_title")
            val = structured_data.get("valuation")
            parts = [title if title else "Term Sheet"]
            if val:
                parts.append(f"Valuation: {val}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.RESUME:
            name = structured_data.get("candidate_name")
            skills = structured_data.get("skills", [])
            parts = [f"Resume for {name}" if name else "Candidate resume"]
            if skills:
                parts.append(f"Skills: {', '.join(skills[:4])}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.REPORT:
            title = structured_data.get("report_title")
            summary = f"Report: {title}." if title else "Operational report."
        elif archetype == DocumentArchetype.POLICY_DOCUMENT:
            title = structured_data.get("policy_title")
            summary = f"Policy document: {title}." if title else "Institutional policy document."
        elif archetype == DocumentArchetype.MEMO:
            subj = structured_data.get("subject") or structured_data.get("memo_title")
            frm = structured_data.get("from_party")
            to = structured_data.get("to_party")
            parts = [f"Memo: {subj}" if subj else "Internal memo"]
            if frm:
                parts.append(f"from {frm}")
            if to:
                parts.append(f"to {to}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.LETTER:
            subj = structured_data.get("subject") or structured_data.get("letter_title")
            summary = f"Letter: {subj}." if subj else "Formal letter."
        elif archetype == DocumentArchetype.SPECIFICATION:
            title = structured_data.get("spec_title")
            ver = structured_data.get("version")
            parts = [f"Specification: {title}" if title else "Technical specification"]
            if ver:
                parts.append(f"v{ver}")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.MEETING_MINUTES:
            title = structured_data.get("meeting_title")
            date = structured_data.get("date")
            parts = [f"Meeting minutes: {title}" if title else "Meeting minutes"]
            if date:
                parts.append(f"({date})")
            summary = " ".join(parts) + "."
        elif archetype == DocumentArchetype.PROPOSAL:
            title = structured_data.get("proposal_title")
            val = structured_data.get("total_value")
            parts = [f"Proposal: {title}" if title else "Business proposal"]
            if val:
                parts.append(f"Value: {val}")
            summary = " ".join(parts) + "."

        operational: list[EvidenceClause] = []
        obligations: list[EvidenceClause] = []
        deliverables: list[EvidenceClause] = []
        liabilities: list[EvidenceClause] = []

        if archetype in (DocumentArchetype.CONTRACT, DocumentArchetype.NDA):
            obligations = [EvidenceClause(**o) if isinstance(o, dict) else o for o in structured_data.get("core_obligations", []) or structured_data.get("obligations", [])]
            liabilities = [EvidenceClause(**l) if isinstance(l, dict) else l for l in structured_data.get("liability_clauses", [])]
            operational = [EvidenceClause(**t) if isinstance(t, dict) else t for t in structured_data.get("termination_terms", [])]
        elif archetype == DocumentArchetype.INVOICE:
            if structured_data.get("due_date"):
                operational.append(EvidenceClause(text=f"Payment due: {structured_data['due_date']}", page=1, category="Payment Deadline"))
            if structured_data.get("payment_terms"):
                operational.append(EvidenceClause(text=f"Payment terms: {structured_data['payment_terms']}", page=1, category="Terms"))
            for item in structured_data.get("line_items", [])[:4]:
                desc = item.get("description") if isinstance(item, dict) else item.description
                if desc:
                    deliverables.append(EvidenceClause(text=desc, page=1, category="Deliverable"))
        elif archetype == DocumentArchetype.REPORT:
            highlights = structured_data.get("executive_highlights", [])
            operational = [EvidenceClause(**h) if isinstance(h, dict) else h for h in highlights]
            for m in structured_data.get("key_metrics", [])[:4]:
                m_txt = f"{m.get('metric')}: {m.get('value')}" if isinstance(m, dict) else f"{m.metric}: {m.value}"
                deliverables.append(EvidenceClause(text=m_txt, page=1, category="Metric"))
        elif archetype == DocumentArchetype.PROPOSAL:
            obligations = [EvidenceClause(**o) if isinstance(o, dict) else o for o in structured_data.get("scope_of_work", [])]
            deliverables = [EvidenceClause(**d) if isinstance(d, dict) else d for d in structured_data.get("deliverables", [])]
        elif archetype == DocumentArchetype.MEETING_MINUTES:
            obligations = [EvidenceClause(**o) if isinstance(o, dict) else o for o in structured_data.get("action_items", [])]
            operational = [EvidenceClause(**d) if isinstance(d, dict) else d for d in structured_data.get("decisions", [])]
        elif archetype == DocumentArchetype.SPECIFICATION:
            obligations = [EvidenceClause(**o) if isinstance(o, dict) else o for o in structured_data.get("requirements", [])]
            operational = [EvidenceClause(**d) if isinstance(d, dict) else d for d in structured_data.get("technical_constraints", [])]

        if llm_data:
            if "executive_summary" in llm_data and llm_data["executive_summary"]:
                summary = llm_data["executive_summary"]
            if "operational_summary_points" in llm_data and isinstance(llm_data["operational_summary_points"], list):
                operational = [EvidenceClause(**p) if isinstance(p, dict) else EvidenceClause(text=str(p), page=1) for p in llm_data["operational_summary_points"]]
            if "core_obligations" in llm_data and isinstance(llm_data["core_obligations"], list):
                obligations = [EvidenceClause(**o) if isinstance(o, dict) else EvidenceClause(text=str(o), page=1) for o in llm_data["core_obligations"]]
            if "key_deliverables" in llm_data and isinstance(llm_data["key_deliverables"], list):
                deliverables = [EvidenceClause(**d) if isinstance(d, dict) else EvidenceClause(text=str(d), page=1) for d in llm_data["key_deliverables"]]
            if "liability_clauses" in llm_data and isinstance(llm_data["liability_clauses"], list):
                liabilities = [EvidenceClause(**l) if isinstance(l, dict) else EvidenceClause(text=str(l), page=1) for l in llm_data["liability_clauses"]]

        parties_list: list[EntityParty] = []
        if archetype in (DocumentArchetype.CONTRACT, DocumentArchetype.NDA):
            parties_list = [EntityParty(**p) if isinstance(p, dict) else p for p in structured_data.get("contracting_parties", [])]
            if archetype == DocumentArchetype.NDA:
                disc = structured_data.get("disclosing_party")
                recv = structured_data.get("receiving_party")
                if disc:
                    parties_list.append(EntityParty(name=disc, role="Disclosing Party", page=1))
                if recv:
                    parties_list.append(EntityParty(name=recv, role="Receiving Party", page=1))
        elif archetype == DocumentArchetype.TERM_SHEET:
            parties_list = [EntityParty(**p) if isinstance(p, dict) else p for p in structured_data.get("parties", [])]
        elif archetype == DocumentArchetype.INVOICE:
            if structured_data.get("vendor_name"):
                parties_list.append(EntityParty(name=structured_data["vendor_name"], role="Vendor / Payee", page=1))
            if structured_data.get("customer_name"):
                parties_list.append(EntityParty(name=structured_data["customer_name"], role="Client / Debtor", page=1))
        elif archetype == DocumentArchetype.PURCHASE_ORDER:
            if structured_data.get("buyer_name"):
                parties_list.append(EntityParty(name=structured_data["buyer_name"], role="Buyer", page=1))
            if structured_data.get("supplier_name"):
                parties_list.append(EntityParty(name=structured_data["supplier_name"], role="Supplier", page=1))
        elif archetype == DocumentArchetype.RESUME:
            if structured_data.get("candidate_name"):
                parties_list.append(EntityParty(name=structured_data["candidate_name"], role="Candidate", page=1))
        elif archetype == DocumentArchetype.REPORT:
            if structured_data.get("author_or_organization"):
                parties_list.append(EntityParty(name=structured_data["author_or_organization"], role="Authoring Body", page=1))
        elif archetype == DocumentArchetype.PROPOSAL:
            if structured_data.get("submitted_by"):
                parties_list.append(EntityParty(name=structured_data["submitted_by"], role="Proposer", page=1))
            if structured_data.get("submitted_to"):
                parties_list.append(EntityParty(name=structured_data["submitted_to"], role="Client", page=1))
        elif archetype == DocumentArchetype.MEMO:
            if structured_data.get("from_party"):
                parties_list.append(EntityParty(name=structured_data["from_party"], role="Sender", page=1))
            if structured_data.get("to_party"):
                parties_list.append(EntityParty(name=structured_data["to_party"], role="Recipient", page=1))

        terms_list = obligations[:4] if obligations else operational[:4]

        entities = StructuredEntities(
            dates=dates,
            monetary_amounts=monetary,
            parties=parties_list,
            terms=terms_list
        )

        return (
            structured_data,
            entities,
            summary,
            operational,
            obligations,
            deliverables,
            liabilities,
            keywords,
            tags,
            provider_used
        )

extractor_service = ExtractionPipeline()
