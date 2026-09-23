# AI-Powered Document Intelligence System

A production-grade enterprise document intelligence platform featuring multi-format ingestion, automated document archetype classification, strict JSON entity extraction with verbatim page citations, AI-generated executive summaries, SQLite FTS5 corpus search, and split-screen dual-view inspection.

---

## 1. Quick Evaluator Verification

### Live Public Application
Access the currently running live instance:
**`https://writer-yeast-such-such.trycloudflare.com`**

### Instant Test Steps:
1. Open the public URL above in your browser.
2. Click **Upload Document** and drag & drop [`sample_contract.pdf`](file:///D:/ADP/sample_contract.pdf) (located directly in the repository root).
3. Within 2-3 seconds, the dual-view interface will display:
   - **Archetype**: `Contract` (with high confidence score and classification rationale).
   - **Split-Screen View**: The original PDF document preview on the left alongside extracted intelligence on the right.
   - **Executive Summary**: Concise high-signal abstract identifying contracting parties and governing terms.
   - **Entity Extraction & Page Citations**: Dates, monetary amounts, contracting parties, and core obligations with exact `p. 1` page references.
   - **Strict JSON Schema**: Formatted, valid JSON conforming to strict Pydantic schemas with 1-click clipboard copy and file export.
   - **Searchable Corpus**: Immediate FTS5 full-text indexing searchable via the top search bar (`Ctrl+K`).

---

## 2. System Architecture

```
                                    ┌──────────────────────────────────────────────────────────┐
                                    │                     DOCINTEL SYSTEM                      │
                                    └──────────────────────────────────────────────────────────┘
                                                                  │
              ┌───────────────────────────────────────────────────┼───────────────────────────────────────────────────┐
              ▼                                                   ▼                                                   ▼
┌───────────────────────────┐                       ┌───────────────────────────┐                       ┌───────────────────────────┐
│     INGESTION PIPELINE    │                       │   INTELLIGENCE ENGINE     │                       │     DUAL-VIEW INTERFACE   │
├───────────────────────────┤                       ├───────────────────────────┤                       ├───────────────────────────┤
│ • Multi-format Parser     │                       │ • Archetype Classifier    │                       │ • Original Doc Preview    │
│   - Digital PDF (pypdf)   │                       │   - Invoice               │                       │   - PDF iframe viewer     │
│   - DOCX (python-docx)    │                       │   - Resume                │                       │   - Raw stream inspector  │
│   - Scanned Images (OCR)  │────── Raw Text ──────▶│   - Contract              │────── JSON DTOs ─────▶│ • Structured AI Pane      │
│ • Validation Guards       │   (with [PAGE N])     │   - Report                │   (with Page Citations│   - Executive abstract    │
│   - Magic-byte signatures │                       │   - Policy Document       │    & Evidence)        │   - Core obligations      │
│   - MIME-type filters     │                       │ • Strict Entity Parser    │                       │   - Deliverables/Risks    │
│   - 25MB file size limit  │                       │   - Dates, Money, Parties │                       │   - Strict Schema tables  │
│   - Gemini Vision OCR     │                       │ • SQLite FTS5 Search      │                       │   - JSON copy/download    │
└───────────────────────────┘                       │ • Multi-Provider LLM      │                       └───────────────────────────┘
                                                    │   - Gemini / OpenAI / Rule│
                                                    └───────────────────────────┘
```

### Clean Architecture & Directory Structure

```
D:\ADP\
├── backend/
│   ├── app/
│   │   ├── api/routes.py            # REST API endpoints (/documents, /search, /stats, /healthz)
│   │   ├── core/config.py           # Application settings and storage paths
│   │   ├── db/database.py           # SQLite repository with FTS5 indexing and BM25 search
│   │   ├── models/schemas.py        # Strict Pydantic models with EvidenceClause & page citations
│   │   ├── services/
│   │   │   ├── ingestion.py         # Multi-format parser, magic bytes validation & OCR
│   │   │   ├── categorizer.py       # Domain-specific archetype classifier
│   │   │   ├── extractor.py         # Strict entity extractor and multi-provider LLM pipeline
│   │   │   └── seed_data.py         # Programmatic PDF generator and sample data seeder
│   │   └── main.py                  # FastAPI entrypoint, CORS, and SPA static mount
│   ├── tests/
│   │   ├── test_backend.py          # Pytest automated test suite
│   │   └── verify_live.py           # End-to-end integration test runner
│   ├── requirements.txt             # Python backend dependencies
│   └── static/                      # Production compiled Vite frontend bundle
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx           # Utilitarian header with system stats and actions
│   │   │   ├── DocumentList.tsx     # High-density corpus directory with archetype filters
│   │   │   ├── DocumentViewer.tsx   # Split-screen left pane: native PDF/text viewer
│   │   │   ├── IntelligencePane.tsx # Split-screen right pane: structured schema & page citations
│   │   │   ├── CorpusSearchModal.tsx# FTS5 search modal with highlighted snippets
│   │   │   └── UploadModal.tsx      # Secure drag-and-drop file uploader
│   │   ├── services/api.ts          # Type-safe API client
│   │   ├── App.tsx                  # Root layout and split-screen controller
│   │   ├── main.tsx                 # React DOM mount
│   │   └── index.css                # Tailwind base and utilitarian styling
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── samples/                         # Pre-loaded PDF files generated for evaluator verification
│   ├── sample_contract.pdf
│   ├── sample_cloud_invoice.pdf
│   ├── sample_infosec_compliance_policy.pdf
│   ├── sample_master_services_agreement.pdf
│   ├── sample_quarterly_operations_report.pdf
│   └── sample_software_engineer_resume.pdf
├── sample_contract.pdf              # Root-level test contract for immediate upload
├── storage/                         # Local database and uploaded file persistence
├── .env.example                     # Environment variables specification
├── build.sh                         # Cloud deployment build script
├── render.yaml                      # Render Blueprint infrastructure specification
├── run_local.bat                    # One-click Windows launch script
├── run_local.ps1                    # PowerShell launch script
├── start_public_service.bat         # One-click script to start server and public tunnel
└── start.sh                         # Container and production launch script
```

---

## 3. Core Capabilities & Enhancements

### Reliable Multi-Format Ingestion & OCR
- Validates file integrity via **magic bytes** (`%PDF-`, `PK\x03\x04`, `\x89PNG`, `\xff\xd8\xff`).
- Extracts text page-by-page preserving structural page markers `[PAGE 1]`, `[PAGE 2]`.
- Multi-tier OCR fallback: uses Gemini Vision multimodality or local Tesseract for image-only scans.

### Verbatim Evidence & Page References
- Every extracted entity, core obligation, key deliverable, and liability clause contains:
  - `page`: 1-indexed page reference where the term was located.
  - `text`: Verbatim quotation from the document text.
- Displayed prominently in the UI via page badges (`p. 1`, `p. 2`).

### Strict Archetype Categorization
- High-precision classification into 5 standardized archetypes:
  1. **Invoice**: Vendor, customer, invoice #, dates, line items, taxes, totals, payment terms.
  2. **Resume**: Candidate, contact details, experience, skills, education, certifications.
  3. **Contract**: Contracting parties, effective date, governing law, obligations, liabilities.
  4. **Report**: Period, organization, executive highlights, quantitative metrics, findings.
  5. **Policy Document**: Policy ID, regulatory frameworks, compliance rules, penalties.

### Reliable Extraction Pipeline
- Integrates cleanly with **Google Gemini** (`gemini-2.5-flash`) or **OpenAI** (`gpt-4o-mini`).
- Includes a robust deterministic fallback rule engine that parses genuine text lines and patterns without inventing hallucinated default names or monetary values when running offline.

### Utilitarian & Minimal Interface
- Prioritizes high information density, clean typography (Inter / JetBrains Mono), fast interaction speeds, and zero distracting animations.

---

## 4. Local Installation & Launch

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### One-Click Launch (Windows)
Double-click `run_local.bat` or run:
```powershell
.\run_local.bat
```

To launch both the server and a public Cloudflare tunnel:
```cmd
start_public_service.bat
```

### Manual Launch

1. **Backend**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests -v
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

2. **Frontend**:
```bash
cd frontend
npm install
npm run build
```

The production application is served at `http://127.0.0.1:8000`.

---

## 5. Render Public Cloud Deployment

This repository is ready for deployment on **Render** as a single unified web service.

### Deployment Steps:
1. Create a GitHub repository and push this directory.
2. In the [Render Dashboard](https://dashboard.render.com/), select **New** > **Blueprint**.
3. Connect your repository. Render automatically processes [`render.yaml`](file:///D:/ADP/render.yaml):
   - **Runtime**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
4. Set optional API keys in the Render environment settings (`GEMINI_API_KEY` or `OPENAI_API_KEY`).
5. Render builds the Vite frontend, copies static assets into FastAPI, installs Python packages, and brings the service live.

### Health Check
Render monitors service uptime via:
```
GET /api/healthz
```

---

## 6. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/healthz` | Service health check and uptime status |
| `GET` | `/api/stats` | System metrics (archetype breakdown, storage size, active engine) |
| `GET` | `/api/documents` | List ingested documents with optional archetype filter |
| `GET` | `/api/documents/{id}` | Retrieve complete structured intelligence with page citations |
| `GET` | `/api/documents/{id}/file` | Stream original file for split-screen inline viewer |
| `POST` | `/api/documents/upload` | Upload and analyze a document (`multipart/form-data`) |
| `DELETE` | `/api/documents/{id}` | Remove document and delete disk storage |
| `POST` | `/api/documents/seed` | Seed / re-seed sample documents |
| `GET` | `/api/search` | FTS5 full-text corpus search with query and filters |
| `GET` | `/api/docs` | Interactive OpenAPI Swagger UI |
