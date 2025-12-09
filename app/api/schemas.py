from typing import Optional
from pydantic import BaseModel


class CSVDataBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    salary: Optional[float] = None


class CSVDataCreate(CSVDataBase):
    pass


class CSVDataUpdate(CSVDataBase):
    pass


class CSVData(CSVDataBase):
    id: int

    class Config:
        orm_mode = True
