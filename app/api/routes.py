from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.celery_config import celery_app
from app.database.connection import get_db
from app.database.models import CSVData
from app.api import schemas

import os
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and trigger celery task"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        task = celery_app.send_task("process_csv_file", args=[str(file_path)])

        return JSONResponse(
            status_code=202,
            content={
                "message": "File uploaded successfully.",
                "task_id": task.id,
                "status": "Processing started",
            },
        )

    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Check status of Celery Task"""
    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        response = {
            "task_id": task_id,
            "state": task.state,
            "status": "Task is waiting to process.",
        }
    elif task.state != "SUCCESS":
        response = {"task_id": task_id, "state": task.state, "result": task.result}
    elif task.state == "FAILIRE":
        response = {"task_id": task_id, "state": task.state, "error": str(task.info)}
    else:
        response = {"task_id": task_id, "state": task.state, "status": str(task.info)}

    return response


# ------------------ CRED (Create, Read, Edit, Delete) endpoints ------------------


@router.post("/records/", response_model=schemas.CSVData)
def create_record(payload: schemas.CSVDataCreate, db: Session = Depends(get_db)):
    """Create a CSVData record"""
    record = CSVData(**payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/records/", response_model=List[schemas.CSVData])
def list_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List CSVData records"""
    records = db.query(CSVData).offset(skip).limit(limit).all()
    return records


@router.get("/records/{record_id}", response_model=schemas.CSVData)
def get_record(record_id: int, db: Session = Depends(get_db)):
    """Get a single CSVData record by id"""
    record = db.get(CSVData, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/records/{record_id}", response_model=schemas.CSVData)
def update_record(record_id: int, payload: schemas.CSVDataUpdate, db: Session = Depends(get_db)):
    """Update an existing CSVData record"""
    record = db.get(CSVData, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a CSVData record"""
    record = db.get(CSVData, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()
    return Response(status_code=204)