export type DocumentArchetype =
  | 'Invoice'
  | 'Resume'
  | 'Contract'
  | 'Report'
  | 'Policy Document'
  | 'Memo'
  | 'Purchase Order'
  | 'Non-Disclosure Agreement'
  | 'Term Sheet'
  | 'Letter'
  | 'Specification'
  | 'Meeting Minutes'
  | 'Proposal';

export interface EntityDate {
  value: string;
  context: string;
  page: number;
}

export interface EntityMonetary {
  amount: number;
  currency: string;
  context: string;
  page: number;
}

export interface EntityParty {
  name: string;
  role: string;
  details?: string;
  page: number;
}

export interface EvidenceClause {
  text: string;
  page: number;
  category?: string;
  confidence: number;
}

export interface StructuredEntities {
  dates: EntityDate[];
  monetary_amounts: EntityMonetary[];
  parties: EntityParty[];
  terms: EvidenceClause[];
}

export interface DocumentIntelligence {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  upload_timestamp: string;
  file_url: string;
  archetype: DocumentArchetype;
  archetype_confidence: number;
  archetype_rationale: string;
  executive_summary: string;
  operational_summary_points: EvidenceClause[];
  core_obligations: EvidenceClause[];
  key_deliverables: EvidenceClause[];
  liability_clauses: EvidenceClause[];
  extracted_entities: StructuredEntities;
  structured_data: Record<string, any>;
  critical_keywords: string[];
  technical_tags: string[];
  extracted_text_preview: string;
  extracted_text_full: string;
  processing_time_ms: number;
  llm_provider_used: string;
}

export interface DocumentSummaryItem {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  page_count: number;
  upload_timestamp: string;
  file_url: string;
  archetype: DocumentArchetype;
  archetype_confidence: number;
  executive_summary: string;
  critical_keywords: string[];
  processing_time_ms: number;
}

export interface SearchResultItem {
  id: string;
  filename: string;
  archetype: DocumentArchetype;
  upload_timestamp: string;
  page_count: number;
  snippet: string;
  match_score: number;
  critical_keywords: string[];
  executive_summary: string;
}

export interface SearchResponse {
  total: number;
  results: SearchResultItem[];
}

export interface SystemStats {
  total_documents: number;
  archetype_counts: Record<string, number>;
  storage_size_bytes: number;
  active_llm_engine: string;
  uptime_status: string;
}

const API_BASE = '/api';

export async function fetchDocuments(archetype?: string): Promise<DocumentSummaryItem[]> {
  const url = archetype && archetype !== 'All' 
    ? `${API_BASE}/documents?archetype=${encodeURIComponent(archetype)}`
    : `${API_BASE}/documents`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function fetchDocumentById(id: string): Promise<DocumentIntelligence> {
  const res = await fetch(`${API_BASE}/documents/${id}`);
  if (!res.ok) throw new Error('Failed to fetch document details');
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentIntelligence> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
}

export async function seedSampleDocuments(overwrite = false): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/seed?overwrite=${overwrite}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to seed documents');
}

export async function searchCorpus(query: string, archetype?: string, tag?: string): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (archetype && archetype !== 'All') params.append('archetype', archetype);
  if (tag) params.append('tag', tag);
  const res = await fetch(`${API_BASE}/search?${params.toString()}`);
  if (!res.ok) throw new Error('Search failed');
  return res.json();
}

export async function fetchSystemStats(): Promise<SystemStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to fetch system stats');
  return res.json();
}
