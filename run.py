"""One-click launcher for the Intelligent Data Analysis System."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import uvicorn
    from backend.database import init_db

    print("=" * 50)
    print("  智能数据分析系统 v1.0")
    print("  http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("=" * 50)

    init_db()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
