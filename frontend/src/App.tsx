import { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { DocumentList } from './components/DocumentList';
import { DocumentViewer } from './components/DocumentViewer';
import { IntelligencePane } from './components/IntelligencePane';
import { CorpusSearchModal } from './components/CorpusSearchModal';
import { UploadModal } from './components/UploadModal';
import {
  fetchDocuments,
  fetchDocumentById,
  deleteDocument,
  seedSampleDocuments,
  fetchSystemStats,
  DocumentSummaryItem,
  DocumentIntelligence,
  SystemStats
} from './services/api';

export function App() {
  const [documents, setDocuments] = useState<DocumentSummaryItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<DocumentIntelligence | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [selectedArchetype, setSelectedArchetype] = useState('All');
  const [listLoading, setListLoading] = useState(false);
  const [docLoading, setDocLoading] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('docsphere-theme');
    return saved ? saved === 'dark' : true;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      root.classList.remove('light');
      document.body.style.backgroundColor = '#0b0f19';
      document.body.style.color = '#f1f5f9';
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
      document.body.style.backgroundColor = '#f8fafc';
      document.body.style.color = '#0f172a';
    }
    localStorage.setItem('docsphere-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const loadStats = useCallback(async () => {
    try {
      const s = await fetchSystemStats();
      setStats(s);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const loadDocuments = useCallback(async (arch: string = 'All') => {
    setListLoading(true);
    try {
      const docs = await fetchDocuments(arch);
      setDocuments(docs);
      if (docs.length > 0 && !selectedId) {
        setSelectedId(docs[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setListLoading(false);
    }
  }, [selectedId]);

  const loadDocumentDetails = useCallback(async (id: string) => {
    setDocLoading(true);
    try {
      const d = await fetchDocumentById(id);
      setSelectedDoc(d);
    } catch (e) {
      console.error(e);
    } finally {
      setDocLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments(selectedArchetype);
    loadStats();
  }, [loadDocuments, loadStats, selectedArchetype]);

  useEffect(() => {
    if (selectedId) {
      loadDocumentDetails(selectedId);
    } else {
      setSelectedDoc(null);
    }
  }, [selectedId, loadDocumentDetails]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSelectDoc = (id: string) => {
    setSelectedId(id);
  };

  const handleDeleteDoc = async (id: string) => {
    try {
      await deleteDocument(id);
      if (selectedId === id) {
        setSelectedId(null);
        setSelectedDoc(null);
      }
      await loadDocuments(selectedArchetype);
      await loadStats();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSeedData = async () => {
    setIsSeeding(true);
    try {
      await seedSampleDocuments(true);
      await loadDocuments(selectedArchetype);
      await loadStats();
      const freshDocs = await fetchDocuments(selectedArchetype);
      if (freshDocs.length > 0) {
        setSelectedId(freshDocs[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleDocumentUploaded = async (newDoc: DocumentIntelligence) => {
    await loadDocuments(selectedArchetype);
    await loadStats();
    setSelectedId(newDoc.id);
    setSelectedDoc(newDoc);
  };

  const rootCls = isDark
    ? 'h-screen w-screen flex flex-col bg-[#0b0f19] text-slate-100 overflow-hidden font-sans'
    : 'h-screen w-screen flex flex-col bg-slate-50 text-slate-900 overflow-hidden font-sans';

  return (
    <div className={rootCls}>
      <Header
        stats={stats}
        onOpenUpload={() => setUploadOpen(true)}
        onOpenSearch={() => setSearchOpen(true)}
        onSeedData={handleSeedData}
        isSeeding={isSeeding}
        isDark={isDark}
        onToggleTheme={() => setIsDark((v) => !v)}
      />

      <div className="flex-1 flex overflow-hidden">
        <DocumentList
          documents={documents}
          selectedId={selectedId}
          onSelect={handleSelectDoc}
          onDelete={handleDeleteDoc}
          selectedArchetype={selectedArchetype}
          onSelectArchetype={setSelectedArchetype}
          loading={listLoading}
          isDark={isDark}
        />

        <div className="flex-1 flex overflow-hidden">
          <div className="w-1/2 h-full">
            <DocumentViewer
              document={selectedDoc}
              loading={docLoading}
              isDark={isDark}
            />
          </div>

          <div className="w-1/2 h-full">
            <IntelligencePane
              document={selectedDoc}
              loading={docLoading}
              isDark={isDark}
            />
          </div>
        </div>
      </div>

      <CorpusSearchModal
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelectDocument={handleSelectDoc}
        isDark={isDark}
      />

      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploaded={handleDocumentUploaded}
        isDark={isDark}
      />
    </div>
  );
}

export default App;
