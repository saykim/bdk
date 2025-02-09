import sqlite3
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# SQLite 데이터베이스 설정
DB_FILE = "process_map.db"

# DB 파일이 없으면 생성
if not os.path.isfile(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE diagrams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diagram_name TEXT NOT NULL,
            diagram_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/save_diagram")
async def save_diagram(payload: dict):
    name = payload.get("name")
    data = payload.get("data")
    if not name or not data:
        return JSONResponse({"success": False, "message": "Invalid data"})

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT id FROM diagrams WHERE diagram_name = ?", (name,))
        existing = c.fetchone()
        
        if existing:
            c.execute("""
                UPDATE diagrams 
                SET diagram_data = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (data, existing[0]))
        else:
            c.execute("""
                INSERT INTO diagrams (diagram_name, diagram_data) 
                VALUES (?, ?)
            """, (name, data))
        
        conn.commit()
        return JSONResponse({"success": True, "message": "Diagram saved successfully"})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.get("/api/load_diagram")
async def load_diagram(name: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT diagram_data FROM diagrams WHERE diagram_name = ?", (name,))
        result = c.fetchone()
        
        if result:
            return JSONResponse({"success": True, "data": result[0]})
        return JSONResponse({"success": False, "message": "Diagram not found"})
    finally:
        conn.close()

@app.get("/api/list_diagrams")
async def list_diagrams():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute("SELECT diagram_name, created_at, updated_at FROM diagrams ORDER BY updated_at DESC")
        diagrams = [{"name": row[0], "created_at": row[1], "updated_at": row[2]} for row in c.fetchall()]
        return JSONResponse({"success": True, "diagrams": diagrams})
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 