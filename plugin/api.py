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
        main_result_dict = {}
        def get_data_with_children(parent_dict, table, id, session, relation='id'):
            query = text(f"SELECT * FROM public.{table} WHERE {relation} = :id")
            result_query = session.execute(query, {"id": id}).all()

            if result_query:
                result = [i._asdict() for i in result_query]

                #Find children tables
                children_query = text(
                    f"SELECT conname AS constraint_name, conrelid::regclass AS table_name FROM pg_constraint WHERE confrelid = '{table}'::regclass;"
                )
                children_result = session.execute(children_query).all()

                #Fetch data for children
                for res in result:
                    for row in children_result:
                        constraint_name, child_table_name = row
                        res[child_table_name] = {}
                        res[child_table_name] = get_data_with_children(res[child_table_name], child_table_name, res['id'], session, relation=f'{table}_id')
                return result
            else:
                return []  # No data found for the parent table

        main_result_dict[table] = get_data_with_children(main_result_dict, table, id, session)

        return main_result_dict

