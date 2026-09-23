import json
import sqlite3
from typing import Any
from pathlib import Path
from app.core.config import settings
from app.models.schemas import (
    DocumentIntelligence,
    DocumentSummaryItem,
    SearchResultItem,
    SearchResponse,
    SystemStats,
    DocumentArchetype
)

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            page_count INTEGER NOT NULL DEFAULT 1,
            file_path TEXT NOT NULL,
            file_url TEXT NOT NULL,
            upload_timestamp TEXT NOT NULL,
            archetype TEXT NOT NULL,
            archetype_confidence REAL NOT NULL,
            archetype_rationale TEXT NOT NULL,
            executive_summary TEXT NOT NULL,
            operational_summary_points_json TEXT NOT NULL,
            core_obligations_json TEXT NOT NULL,
            key_deliverables_json TEXT NOT NULL,
            liability_clauses_json TEXT NOT NULL,
            extracted_entities_json TEXT NOT NULL,
            structured_data_json TEXT NOT NULL,
            critical_keywords_json TEXT NOT NULL,
            technical_tags_json TEXT NOT NULL,
            extracted_text_preview TEXT NOT NULL,
            extracted_text_full TEXT NOT NULL,
            processing_time_ms REAL NOT NULL,
            llm_provider_used TEXT NOT NULL
        )
    """)
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN page_count INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            id UNINDEXED,
            filename,
            archetype,
            executive_summary,
            extracted_text,
            keywords,
            tags
        )
    """)
    conn.commit()
    conn.close()

init_db()

def serialize_item(item: Any) -> Any:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return item

def save_document(doc: DocumentIntelligence, file_path: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    op_points = [serialize_item(x) for x in doc.operational_summary_points]
    core_obs = [serialize_item(x) for x in doc.core_obligations]
    key_delivs = [serialize_item(x) for x in doc.key_deliverables]
    liab_clauses = [serialize_item(x) for x in doc.liability_clauses]

    cursor.execute(
        """
        INSERT OR REPLACE INTO documents (
            id, filename, file_type, file_size_bytes, page_count, file_path, file_url,
            upload_timestamp, archetype, archetype_confidence, archetype_rationale,
            executive_summary, operational_summary_points_json, core_obligations_json,
            key_deliverables_json, liability_clauses_json, extracted_entities_json,
            structured_data_json, critical_keywords_json, technical_tags_json,
            extracted_text_preview, extracted_text_full, processing_time_ms, llm_provider_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc.id,
            doc.filename,
            doc.file_type,
            doc.file_size_bytes,
            doc.page_count,
            str(file_path),
            doc.file_url,
            doc.upload_timestamp,
            doc.archetype.value,
            doc.archetype_confidence,
            doc.archetype_rationale,
            doc.executive_summary,
            json.dumps(op_points),
            json.dumps(core_obs),
            json.dumps(key_delivs),
            json.dumps(liab_clauses),
            json.dumps(doc.extracted_entities.model_dump()),
            json.dumps(doc.structured_data),
            json.dumps(doc.critical_keywords),
            json.dumps(doc.technical_tags),
            doc.extracted_text_preview,
            doc.extracted_text_full,
            doc.processing_time_ms,
            doc.llm_provider_used
        )
    )
    cursor.execute("DELETE FROM documents_fts WHERE id = ?", (doc.id,))
    cursor.execute(
        """
        INSERT INTO documents_fts (id, filename, archetype, executive_summary, extracted_text, keywords, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc.id,
            doc.filename,
            doc.archetype.value,
            doc.executive_summary,
            doc.extracted_text_full,
            " ".join(doc.critical_keywords),
            " ".join(doc.technical_tags)
        )
    )
    conn.commit()
    conn.close()

def get_document(doc_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    return {
        "id": d["id"],
        "filename": d["filename"],
        "file_type": d["file_type"],
        "file_size_bytes": d["file_size_bytes"],
        "page_count": d.get("page_count", 1),
        "file_path": d["file_path"],
        "file_url": d["file_url"],
        "upload_timestamp": d["upload_timestamp"],
        "archetype": d["archetype"],
        "archetype_confidence": d["archetype_confidence"],
        "archetype_rationale": d["archetype_rationale"],
        "executive_summary": d["executive_summary"],
        "operational_summary_points": json.loads(d["operational_summary_points_json"]),
        "core_obligations": json.loads(d["core_obligations_json"]),
        "key_deliverables": json.loads(d["key_deliverables_json"]),
        "liability_clauses": json.loads(d["liability_clauses_json"]),
        "extracted_entities": json.loads(d["extracted_entities_json"]),
        "structured_data": json.loads(d["structured_data_json"]),
        "critical_keywords": json.loads(d["critical_keywords_json"]),
        "technical_tags": json.loads(d["technical_tags_json"]),
        "extracted_text_preview": d["extracted_text_preview"],
        "extracted_text_full": d["extracted_text_full"],
        "processing_time_ms": d["processing_time_ms"],
        "llm_provider_used": d["llm_provider_used"]
    }

def list_documents(archetype: str | None = None, limit: int = 100, offset: int = 0) -> list[DocumentSummaryItem]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if archetype:
        cursor.execute(
            """
            SELECT id, filename, file_type, file_size_bytes, page_count, file_url, upload_timestamp,
                   archetype, archetype_confidence, executive_summary, critical_keywords_json, processing_time_ms
            FROM documents
            WHERE archetype = ?
            ORDER BY upload_timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (archetype, limit, offset)
        )
    else:
        cursor.execute(
            """
            SELECT id, filename, file_type, file_size_bytes, page_count, file_url, upload_timestamp,
                   archetype, archetype_confidence, executive_summary, critical_keywords_json, processing_time_ms
            FROM documents
            ORDER BY upload_timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        result.append(
            DocumentSummaryItem(
                id=d["id"],
                filename=d["filename"],
                file_type=d["file_type"],
                file_size_bytes=d["file_size_bytes"],
                page_count=d.get("page_count", 1),
                file_url=d["file_url"],
                upload_timestamp=d["upload_timestamp"],
                archetype=DocumentArchetype(d["archetype"]),
                archetype_confidence=d["archetype_confidence"],
                executive_summary=d["executive_summary"],
                critical_keywords=json.loads(d["critical_keywords_json"]),
                processing_time_ms=d["processing_time_ms"]
            )
        )
    return result

def search_documents(query: str = "", archetype: str | None = None, tag: str | None = None, limit: int = 50, offset: int = 0) -> SearchResponse:
    conn = get_db_connection()
    cursor = conn.cursor()
    query_clean = query.strip().replace('"', '""')
    if query_clean:
        fts_query = f'"{query_clean}"' if " " in query_clean else f"{query_clean}*"
        base_sql = """
            SELECT d.id, d.filename, d.archetype, d.page_count, d.upload_timestamp, d.executive_summary,
                   d.critical_keywords_json, snippet(documents_fts, 4, '<b>', '</b>', '...', 20) as match_snippet,
                   bm25(documents_fts) as rank
            FROM documents_fts fts
            JOIN documents d ON d.id = fts.id
            WHERE documents_fts MATCH ?
        """
        params = [fts_query]
        if archetype:
            base_sql += " AND d.archetype = ?"
            params.append(archetype)
        if tag:
            base_sql += " AND (d.critical_keywords_json LIKE ? OR d.technical_tags_json LIKE ?)"
            params.extend([f"%{tag}%", f"%{tag}%"])
        base_sql += " ORDER BY rank LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        try:
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            cursor.execute(
                """
                SELECT id, filename, archetype, page_count, upload_timestamp, executive_summary,
                       critical_keywords_json, SUBSTR(extracted_text_full, 1, 200) as match_snippet, 1.0 as rank
                FROM documents
                WHERE (filename LIKE ? OR extracted_text_full LIKE ? OR executive_summary LIKE ?)
                """ + (" AND archetype = ?" if archetype else "") + " ORDER BY upload_timestamp DESC LIMIT ? OFFSET ?",
                [f"%{query_clean}%", f"%{query_clean}%", f"%{query_clean}%"] + ([archetype] if archetype else []) + [limit, offset]
            )
            rows = cursor.fetchall()
    else:
        sql = "SELECT id, filename, archetype, page_count, upload_timestamp, executive_summary, critical_keywords_json, SUBSTR(extracted_text_full, 1, 200) as match_snippet, 1.0 as rank FROM documents WHERE 1=1"
        params = []
        if archetype:
            sql += " AND archetype = ?"
            params.append(archetype)
        if tag:
            sql += " AND (critical_keywords_json LIKE ? OR technical_tags_json LIKE ?)"
            params.extend([f"%{tag}%", f"%{tag}%"])
        sql += " ORDER BY upload_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        results.append(
            SearchResultItem(
                id=d["id"],
                filename=d["filename"],
                archetype=DocumentArchetype(d["archetype"]),
                upload_timestamp=d["upload_timestamp"],
                page_count=d.get("page_count", 1),
                snippet=d.get("match_snippet") or d.get("executive_summary", "")[:200],
                match_score=float(d.get("rank", 1.0)),
                critical_keywords=json.loads(d["critical_keywords_json"]),
                executive_summary=d["executive_summary"]
            )
        )
    conn.close()
    return SearchResponse(total=len(results), results=results)

def delete_document(doc_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    file_path = Path(row["file_path"])
    if file_path.exists():
        file_path.unlink(missing_ok=True)
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    cursor.execute("DELETE FROM documents_fts WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return True

def get_system_stats() -> SystemStats:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(file_size_bytes), 0) FROM documents")
    total_docs, total_bytes = cursor.fetchone()
    cursor.execute("SELECT archetype, COUNT(*) FROM documents GROUP BY archetype")
    archetype_rows = cursor.fetchall()
    conn.close()
    counts = {r[0]: r[1] for r in archetype_rows}
    for arch in DocumentArchetype:
        if arch.value not in counts:
            counts[arch.value] = 0
    active_engine = "Gemini" if settings.GEMINI_API_KEY else ("OpenAI" if settings.OPENAI_API_KEY else "Deterministic Engine")
    return SystemStats(
        total_documents=total_docs or 0,
        archetype_counts=counts,
        storage_size_bytes=total_bytes or 0,
        active_llm_engine=active_engine,
        uptime_status="HEALTHY"
    )
