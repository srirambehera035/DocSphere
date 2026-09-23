import re
from app.models.schemas import DocumentArchetype

class CategorizationResult:
    def __init__(self, archetype: DocumentArchetype, confidence: float, rationale: str):
        self.archetype = archetype
        self.confidence = confidence
        self.rationale = rationale

class DocumentCategorizer:
    KEYWORDS = {
        DocumentArchetype.INVOICE: [
            "invoice", "bill to", "ship to", "due date", "amount due", "subtotal",
            "invoice number", "inv#", "remit to", "unit price",
            "line item", "vat", "gst", "balance due", "payment terms", "net 30"
        ],
        DocumentArchetype.PURCHASE_ORDER: [
            "purchase order", "po number", "po #", "vendor", "buyer", "supplier",
            "ordered by", "ship to", "quantity ordered", "unit cost", "order total",
            "delivery date", "requisition", "procurement"
        ],
        DocumentArchetype.RESUME: [
            "curriculum vitae", "resume", "experience", "education", "skills",
            "work experience", "employment history", "professional summary", "qualifications",
            "bachelor", "master", "phd", "university", "linkedin", "github", "certifications", "projects"
        ],
        DocumentArchetype.CONTRACT: [
            "agreement", "contract", "parties", "hereby agrees", "whereas", "in witness whereof",
            "terms and conditions", "governing law", "confidentiality", "indemnification",
            "termination", "liability", "effective date", "intellectual property", "breach", "jurisdiction"
        ],
        DocumentArchetype.NDA: [
            "non-disclosure", "nda", "confidentiality agreement", "proprietary information",
            "trade secret", "disclosing party", "receiving party", "confidential information",
            "shall not disclose", "non-disclosure agreement"
        ],
        DocumentArchetype.TERM_SHEET: [
            "term sheet", "letter of intent", "loi", "valuation", "pre-money", "post-money",
            "investment amount", "equity stake", "board seat", "liquidation preference",
            "anti-dilution", "vesting schedule", "series a", "series b"
        ],
        DocumentArchetype.REPORT: [
            "annual report", "quarterly report", "financial report", "status report",
            "executive summary", "key findings", "metrics", "methodology", "analysis",
            "conclusion", "table of contents", "overview", "recommendations", "kpi", "performance"
        ],
        DocumentArchetype.POLICY_DOCUMENT: [
            "policy", "standard operating procedure", "compliance", "regulatory",
            "acceptable use", "governance", "security policy", "scope", "enforcement",
            "responsibilities", "audit", "violation", "guidelines", "protocol", "iso 27001", "gdpr", "hipaa"
        ],
        DocumentArchetype.MEMO: [
            "memorandum", "memo", "internal memo", "to:", "from:", "subject:", "re:",
            "action required", "please note", "fyi", "for your information",
            "internal communication", "all staff", "all employees"
        ],
        DocumentArchetype.LETTER: [
            "dear", "sincerely", "regards", "yours truly", "to whom it may concern",
            "formal letter", "cover letter", "reference letter", "recommendation letter",
            "offer letter", "demand letter"
        ],
        DocumentArchetype.SPECIFICATION: [
            "specification", "requirements", "technical spec", "system requirements",
            "functional requirements", "non-functional", "use case", "acceptance criteria",
            "api spec", "design specification", "architecture", "data flow", "erd"
        ],
        DocumentArchetype.MEETING_MINUTES: [
            "meeting minutes", "minutes of meeting", "mom", "attendees", "agenda",
            "action items", "action item", "next steps", "decisions made", "resolved",
            "quorum", "presiding", "secretary", "adjourned"
        ],
        DocumentArchetype.PROPOSAL: [
            "proposal", "request for proposal", "rfp", "scope of work", "sow",
            "project proposal", "business proposal", "submitted by", "submitted to",
            "proposed budget", "project timeline", "deliverables", "milestones"
        ]
    }

    FILENAME_SIGNALS = {
        DocumentArchetype.INVOICE: ["invoice"],
        DocumentArchetype.PURCHASE_ORDER: ["po", "purchase_order", "purchaseorder"],
        DocumentArchetype.RESUME: ["resume", "cv"],
        DocumentArchetype.CONTRACT: ["contract", "agreement"],
        DocumentArchetype.NDA: ["nda", "non-disclosure", "confidentiality"],
        DocumentArchetype.TERM_SHEET: ["term_sheet", "termsheet", "loi"],
        DocumentArchetype.REPORT: ["report"],
        DocumentArchetype.POLICY_DOCUMENT: ["policy", "procedure", "sop"],
        DocumentArchetype.MEMO: ["memo", "memorandum"],
        DocumentArchetype.LETTER: ["letter"],
        DocumentArchetype.SPECIFICATION: ["spec", "specification", "requirements"],
        DocumentArchetype.MEETING_MINUTES: ["minutes", "mom", "meeting"],
        DocumentArchetype.PROPOSAL: ["proposal", "rfp"],
    }

    def categorize_text(self, text: str, filename: str = "") -> CategorizationResult:
        text_lower = text.lower()
        filename_lower = filename.lower()
        scores: dict[DocumentArchetype, float] = {k: 0.0 for k in DocumentArchetype}

        for arch, words in self.KEYWORDS.items():
            for w in words:
                count = len(re.findall(r"\b" + re.escape(w) + r"\b", text_lower))
                if count > 0:
                    scores[arch] += min(count * 2.0, 10.0)

        for arch, signals in self.FILENAME_SIGNALS.items():
            for sig in signals:
                if sig in filename_lower:
                    scores[arch] += 15.0
                    break

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_arch, best_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

        if best_score <= 1.0:
            return CategorizationResult(
                archetype=DocumentArchetype.REPORT,
                confidence=0.50,
                rationale="Defaulted to Report due to low domain-specific keyword presence."
            )

        margin = best_score - second_score
        confidence = min(0.99, max(0.65, 0.60 + (margin / (best_score + 1.0)) * 0.35))
        matched = [w for w in self.KEYWORDS[best_arch] if re.search(r"\b" + re.escape(w) + r"\b", text_lower)]
        rationale = f"Classified as {best_arch.value} based on prominent signals: {', '.join(matched[:5])}."

        return CategorizationResult(archetype=best_arch, confidence=round(confidence, 2), rationale=rationale)

categorizer = DocumentCategorizer()
