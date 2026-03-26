from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .health import router as health_router
from .websocket import router as ws_router
from .routes.quote import router as quote_router
from .routes.macro import router as macro_router
from .routes.ingest import router as ingest_router

app = FastAPI(title="HHBFin API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(ws_router, tags=["websocket"])
app.include_router(quote_router)
app.include_router(macro_router)
app.include_router(ingest_router)


@app.get("/")
def root():
    return {"status": "HHBFIN TERMINAL API"}
