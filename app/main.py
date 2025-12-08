from fastapi import FastAPI
from app.api.routes import router 
from app.database.connection import engine
from app.database.models import Base


Base.metadata.create_all(bind=engine)

app = FastAPI(title="CSV Processing API")

app.include_router(router, prefix="/api", tags=["CSV Processing"])

@app.get("/")
def read_root():
    return {"message": "Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}