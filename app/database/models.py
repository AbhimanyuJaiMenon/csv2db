from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class CSVData(Base):
    __tablename__ = "csv_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    salary = Column(Float, nullable=True)