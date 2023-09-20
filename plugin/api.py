from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db_session
from typing import List, Any
from uuid import UUID
from sqlalchemy import MetaData, Table
from plugin.models import Base
router = APIRouter()
from sqlalchemy import select, text

@router.get('/{id}', response_model=Any)
def get_data(id: UUID, table: str = None, session: Session = Depends(get_db_session)):
    engine = session.get_bind()
    metadata_obj = MetaData()
    metadata_obj.reflect(bind=engine)
    allowed_tables = [i for i in metadata_obj.tables]
    if table not in allowed_tables:
        raise HTTPException(status_code=404, detail=f'Table {table} not found')
    else:
        table_obj = Table(table, metadata_obj)
        query = text(f"SELECT * FROM public.{table} WHERE id = :id")
        result = session.execute(query, {"id": id}).fetchone()
        if result:
            return dict(result)
        else:
            return dict()
