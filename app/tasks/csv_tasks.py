import pandas as pd
import os
from app.celery_config import celery_app
from app.database.connection import SessionLocal
from app.database.models import CSVData

@celery_app.task(bind=True, name="process_csv_file")
def process_csv_file(self, file_path: str):
    """
    Process CSV file and insert into database in chunks
    """
    try:
        # Use update_state instead of update
        self.update_state(state="PROCESSING", meta={"status": "Reading CSV file"})
        
        # Read CSV in chunks to handle large files
        chunk_size = 1000
        total_rows = 0
        
        db = SessionLocal()
        
        try:
            # Process CSV in chunks
            for chunk_idx, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
                self.update_state(
                    state="PROCESSING",
                    meta={
                        "status": f"Processing chunk {chunk_idx + 1}",
                        "rows_processed": total_rows
                    }
                )
                
                # Convert DataFrame to list of dicts
                records = chunk.to_dict(orient="records")
                
                # Insert into database
                for record in records:
                    db_record = CSVData(**record)
                    db.add(db_record)
                
                db.commit()
                total_rows += len(chunk)
            
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                "status": "success",
                "rows_processed": total_rows,
                "message": f"Successfully processed {total_rows} rows"
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise e