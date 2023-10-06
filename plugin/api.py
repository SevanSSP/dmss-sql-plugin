from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db_session
from typing import Any
from uuid import UUID
from sqlalchemy import MetaData, Table
from plugin.models import Blueprint, resolve_model
from fastapi.encoders import jsonable_encoder
import os
from sqlalchemy import text
from sqlalchemy.orm import aliased, selectinload
import inspect

router = APIRouter()


@router.get('/{id}', response_model=Any)
def get_data_by_id(id: UUID, table: str = None, levels: int = 1, all: bool = False,
                   session: Session = Depends(get_db_session)):
    engine = session.get_bind()
    metadata_obj = MetaData()
    metadata_obj.reflect(bind=engine)

    allowed_tables = [i for i in metadata_obj.tables if
                      not (i.endswith("_map") or i.endswith("_value") or i == 'alembic_version')]
    if table:
        if table not in allowed_tables:
            raise HTTPException(status_code=404, detail=f"Could not find table {table}")
        else:
            allowed_tables = [table]

    for table in allowed_tables:
        query = text(
            f'SELECT * FROM public."{table}" WHERE id = \'{id}\';'
        )
        result = session.execute(query).first()
        if result:
            for root, _, files in os.walk(os.path.join(os.path.dirname(__file__), '..', 'models')):
                if f'{table}.blueprint.json' in files:
                    # Resolve model from table
                    bp = Blueprint.from_json(os.path.join(root, table))
                    model = resolve_model(bp)

                    # Get top level data
                    parent_alias = aliased(model)
                    if all:
                        #Fetches parent and all children to bottom
                        parent_alias = aliased(model)
                        return jsonable_encoder((
                                                    session.query(model, parent_alias)
                                                    .filter(model.id == parent_alias.id)
                                                    .filter(model.id == id)
                                                    .options(selectinload('*'))
                                                ).first()[0])

                        #Fetches only parent
                    top = (
                        session.query(model, parent_alias)
                        .filter(model.id == parent_alias.id)
                        .filter(model.id == id)
                    ).first()[0]

                        #Iterate trough levels to fetch nested children
                    curr_level = 1
                    obj = [top]
                    while curr_level < levels:
                        for j in obj:
                            new_obj = []
                            for i in inspect.getmembers(j):
                                if 'InstrumentedList' in type(i[1]).__name__:
                                    if len(i[1]) > 0:
                                        new_obj.extend(i[1])
                        curr_level += 1
                        obj = new_obj
                        if not obj:
                            break
                    return jsonable_encoder(top)
    raise HTTPException(status_code=404, detail=f"Could not find ID {id}")
