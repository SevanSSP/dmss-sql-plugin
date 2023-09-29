import json
import os
from typing import TypeVar, Type
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from plugin.models import Blueprint
from plugin.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


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

    for child in children:
        child_obj = create_entity(db, child, commit=False)
        if f'{child_obj.__table__.key}_s' not in data:
            data[f'{child_obj.__table__.key}_s'] = [child_obj]
        else:
            data[f'{child_obj.__table__.key}_s'].append(child_obj)

    obj_in_data = jsonable_encoder(data)
    db_obj = model(**obj_in_data)
    for key, value in data_table.items():
        data_table_model = resolve_model(bp, key)
        for item in value:
            getattr(db_obj, key).append(data_table_model(data=item))

    # todo: getting into issues as described here:
    # todo: https://stackoverflow.com/questions/73122511/flask-sqlalchemy-dict-object-has-no-attribute-sa-instance-state
    # todo: Case ends up with a set of dictionaries in the instrumented lists (children of children added through
    #  relationship)

    db.add(db_obj)
    if commit:
        db.commit()
        db.refresh(db_obj)
    return db_obj


def create_entity_from_file(db: Session, filename: str):
    with open(filename, "r") as json_file:
        entity = json.load(json_file)
        return create_entity(db, entity)


def resolve_blueprint(entity_type: str) -> Blueprint:
    blueprint_path = entity_type.split(':')[1]
    base_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'models'))
    return Blueprint.from_json(os.path.join(base_path, blueprint_path))


def resolve_model(blueprint: Blueprint, data_table_name: str = None) -> Type[ModelType]:
    if not data_table_name:
        if not blueprint.return_model():
            blueprint.generate_models_m2m_rel()

        return blueprint.return_model()
    else:
        if not blueprint.return_data_table_model(data_table_name):
            blueprint.generate_models_m2m_rel()

        return blueprint.return_data_table_model(data_table_name)
