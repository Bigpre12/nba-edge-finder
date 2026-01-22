"""
Ultra-light FastAPI server for Render free tier.
Serves static files + cached JSON proxy.
Single worker, minimal memory footprint.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# === Configuration ===
CACHE_TTL_SECONDS = 60  # Cache JSON for 60 seconds
DATA_DIR = Path("data")
STATIC_DIR = Path("static")

# === In-memory cache ===
_cache: dict = {}
_cache_time: dict = {}

app = FastAPI(
    title="NBA Edge Finder",
    docs_url=None,  # Disable docs to save memory
    redoc_url=None
)


def get_cached(key: str) -> Optional[dict]:
    """Get item from cache if not expired."""
    if key in _cache and key in _cache_time:
        if datetime.utcnow() - _cache_time[key] < timedelta(seconds=CACHE_TTL_SECONDS):
            return _cache[key]
    return None


def set_cached(key: str, value: dict):
    """Set item in cache."""
    _cache[key] = value
    _cache_time[key] = datetime.utcnow()
    
    # Limit cache size to prevent memory bloat
    if len(_cache) > 20:
        oldest_key = min(_cache_time, key=_cache_time.get)
        _cache.pop(oldest_key, None)
        _cache_time.pop(oldest_key, None)


def load_json_file(filename: str) -> dict:
    """Load JSON file with caching."""
    cache_key = f"file:{filename}"
    
    # Check cache first
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    # Load from file
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {"error": "File not found", "updated": None, "count": 0}
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        set_cached(cache_key, data)
        return data
    except Exception as e:
        return {"error": str(e), "updated": None, "count": 0}


def generate_etag(data: dict) -> str:
    """Generate ETag from data."""
    content = json.dumps(data, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()[:16]


def json_response_with_etag(data: dict, request: Request) -> Response:
    """Return JSON with ETag for conditional GET support."""
    etag = generate_etag(data)
    
    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return Response(status_code=304)
    
    return JSONResponse(
        content=data,
        headers={
            "ETag": etag,
            "Cache-Control": f"public, max-age={CACHE_TTL_SECONDS}",
            "Access-Control-Allow-Origin": "*"
        }
    )


# === API Routes ===

@app.get("/api/props")
async def get_props(request: Request):
    """Get all props data."""
    data = load_json_file("props.json")
    return json_response_with_etag(data, request)


@app.get("/api/players")
async def get_players(request: Request):
    """Get players list."""
    data = load_json_file("players.json")
    return json_response_with_etag(data, request)


@app.get("/api/games")
async def get_games(request: Request):
    """Get today's games."""
    data = load_json_file("games.json")
    return json_response_with_etag(data, request)


@app.get("/api/player/{player_id}")
async def get_player(player_id: int, request: Request):
    """Get single player's props."""
    props_data = load_json_file("props.json")
    
    if "error" in props_data:
        raise HTTPException(status_code=404, detail="Props data not found")
    
    # Find player in props
    for prop in props_data.get("props", []):
        if prop.get("id") == player_id:
            return json_response_with_etag({
                "updated": props_data.get("updated"),
                "player": prop
            }, request)
    
    raise HTTPException(status_code=404, detail="Player not found")


@app.get("/api/status")
async def get_status():
    """Health check with data freshness."""
    props = load_json_file("props.json")
    return {
        "status": "ok",
        "updated": props.get("updated"),
        "count": props.get("count", 0),
        "cache_size": len(_cache)
    }


@app.get("/health")
async def health():
    """Simple health check for Render."""
    return {"status": "ok"}


# === Static Files ===

# Serve index.html at root
@app.get("/")
async def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "NBA Edge Finder API", "docs": "/api/status"}


# Mount static files (JS, CSS)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve data files directly (fallback if GitHub raw isn't used)
if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")


# === Startup ===

@app.on_event("startup")
async def startup():
    """Startup tasks."""
    print(f"Starting NBA Edge Finder...")
    print(f"  Data dir: {DATA_DIR.absolute()}")
    print(f"  Static dir: {STATIC_DIR.absolute()}")
    print(f"  Cache TTL: {CACHE_TTL_SECONDS}s")
    
    # Pre-load data into cache
    if (DATA_DIR / "props.json").exists():
        props = load_json_file("props.json")
        print(f"  Loaded {props.get('count', 0)} props from cache")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
