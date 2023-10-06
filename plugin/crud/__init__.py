import json
import os
from typing import TypeVar, Type
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from plugin.models import Blueprint, resolve_blueprint, resolve_model
from plugin.models.base import Base
import time

def create_entity(db: Session, entity: dict, commit=True) -> dict:
    bp = resolve_blueprint(entity['type'])
    model = resolve_model(bp)

    data_table = {}
    children = []
    data = dict()
    for key, value in entity.items():
        attr = [attr for attr in bp.attributes if attr.name == key][0]
        if attr.name == 'type':
            continue
        if attr.attributeType.lower() in ["string", "integer", "number", "float", "boolean", "foreign_key", "type",
                                          "core:blueprintattribute"]:
            if hasattr(attr, 'dimensions') and attr.dimensions == '*':
                data_table[key] = value
            else:
                data[key] = value
        else:
            if isinstance(value, list):
                children.extend(value)
            elif isinstance(value, dict):
                children.append(value)
            else:
                raise NotImplementedError(f'Type {type(value)} not supported yet')

    obj_in_data = jsonable_encoder(data)
    db_obj = model(**obj_in_data)

    for child in children:
        child_obj = create_entity(db, child, commit=True)
        getattr(db_obj, f'{child_obj.__table__.key}_s').append(child_obj)

    for key, value in data_table.items():
        data_table_model = resolve_model(bp, key)
        data_table_objects = [data_table_model(data=item) for item in value]
        getattr(db_obj, key).extend(data_table_objects)

    db.add(db_obj)
    if commit:
        db.commit()
        db.refresh(db_obj)
    return db_obj


def create_entity_from_file(db: Session, filename: str):
    with open(filename, "r") as json_file:
        entity = json.load(json_file)
        return create_entity(db, entity)
