from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.models import models  # noqa
from app.api.routes import router
Base.metadata.create_all(bind=engine)  # local convenience; production uses Alembic (docs)
app=FastAPI(title="LedgerLab API",version="1.0.0",docs_url="/docs")
app.add_middleware(CORSMiddleware,allow_origins=settings.origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.exception_handler(Exception)
async def unhandled(request:Request, exc:Exception):
    if exc.__class__.__name__=="HTTPException": raise exc
    return JSONResponse(status_code=500,content={"detail":{"code":"INTERNAL_ERROR","message":"Something went wrong. No transfer was completed."}})
@app.get("/health")
def health(): return {"status":"ok","service":"LedgerLab","simulation":True}
app.include_router(router)
