import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import (
    DocumentIntelligence,
    DocumentSummaryItem,
    SearchResponse,
    SystemStats,
    DocumentArchetype
)
from app.db.database import (
    save_document,
    get_document,
    list_documents,
    delete_document,
    search_documents,
    get_system_stats
)
from app.services.ingestion import ingestion_service, IngestionError
from app.services.categorizer import categorizer
from app.services.extractor import extractor_service
from app.services.seed_data import seed_sample_documents

router = APIRouter()

@router.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/stats", response_model=SystemStats)
async def system_stats():
    return get_system_stats()

@router.post("/documents/seed")
async def seed_documents(overwrite: bool = Query(False)):
    seeded = await seed_sample_documents(overwrite=overwrite)
    return {
        "message": f"Seeded {len(seeded)} documents successfully",
        "count": len(seeded)
    }

@router.post("/documents/upload", response_model=DocumentIntelligence)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name")

    file_bytes = await file.read()
    file_size = len(file_bytes)

    try:
        ingestion_service.validate_file(
            file.filename,
            file.content_type or "application/octet-stream",
            file_size,
            file_bytes,
            settings.MAX_FILE_SIZE_BYTES
        )
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    t0 = time.perf_counter()

    try:
        raw_text, pages_text, total_pages = ingestion_service.extract(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract document stream: {str(e)}")

    if not raw_text.strip():
        raw_text = f"[PAGE 1]\nDocument text stream from {file.filename} (Zero extractable text detected)."

    cat_result = categorizer.categorize_text(raw_text, file.filename)

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

    safe_filename = Path(file.filename).name
    save_path = settings.UPLOAD_DIR / f"{doc_id}_{safe_filename}"
    save_path.write_bytes(file_bytes)

    doc_obj = DocumentIntelligence(
        id=doc_id,
        filename=safe_filename,
        file_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
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

    save_document(doc_obj, str(save_path))
    return doc_obj

@router.get("/documents", response_model=list[DocumentSummaryItem])
async def get_documents(
    archetype: DocumentArchetype | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    arch_val = archetype.value if archetype else None
    return list_documents(archetype=arch_val, limit=limit, offset=offset)

@router.get("/documents/{doc_id}")
async def get_document_by_id(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/documents/{doc_id}/file")
async def get_document_file(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Underlying file not found on disk")
    return FileResponse(
        path=file_path,
        media_type=doc["file_type"],
        filename=doc["filename"],
        content_disposition_type="inline"
    )

@router.delete("/documents/{doc_id}")
async def delete_document_by_id(doc_id: str):
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully", "id": doc_id}

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query("", alias="q"),
    archetype: DocumentArchetype | None = None,
    tag: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    arch_val = archetype.value if archetype else None
    return search_documents(query=q, archetype=arch_val, tag=tag, limit=limit, offset=offset)
