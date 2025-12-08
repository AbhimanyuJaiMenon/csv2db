from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.celery_config import celery_app
import shutil
import os 
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file and trigger celery task

    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    file_path = UPLOAD_DIR / file.filename

    try:

        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)


        task = celery_app.send_task("process_csv_file", args=[str(file_path)], queue="csv_processing")

        return JSONResponse(
            status_code=202,
            content={
                "message": "File uploaded successfully.",
                "task_id": task.id,
                "status": "Processing started"
            }
        )   
    
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Check status of Celery Task
    """
    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        response = {
            "task_id": task_id,
            "state": task.state,
            "status": "Task is waiting to process."
        }
    elif task.state != "SUCCESS":
        response = {
            "task_id": task_id,
            "state": task.state,
            "result": task.result
        }
    elif task.state == "FAILIRE":
        response = {
            "task_id": task_id,
            "state": task.state,
            "error": str(task.info)
        }
    else:
        response = {
            "task_id": task_id,
            "state": task.state,
            "status": str(task.info)
        }

    return response