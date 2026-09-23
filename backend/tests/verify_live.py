import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from fastapi.testclient import TestClient

def main():
    client = TestClient(app)
    h = client.get("/api/healthz")
    assert h.status_code == 200
    print("HEALTH CHECK:", h.json())

    docs = client.get("/api/documents")
    assert docs.status_code == 200
    docs_data = docs.json()
    print("DOCUMENTS COUNT:", len(docs_data))
    for d in docs_data:
        print(f" - {d['archetype']}: {d['filename']} (Confidence: {d['archetype_confidence']})")

    stats = client.get("/api/stats")
    assert stats.status_code == 200
    print("SYSTEM STATS:", stats.json())

    search = client.get("/api/search?q=agreement")
    assert search.status_code == 200
    search_data = search.json()
    print("SEARCH RESULTS FOR 'agreement':", search_data["total"])

    static_res = client.get("/")
    assert static_res.status_code == 200
    print("STATIC FRONTEND ROOT SERVED:", len(static_res.text), "bytes")

if __name__ == "__main__":
    main()
