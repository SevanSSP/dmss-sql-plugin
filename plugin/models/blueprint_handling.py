from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Optional
from alembic.config import Config
from alembic import command
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.ext.orderinglist import ordering_list
import os
from datetime import datetime

from .base import Base

"""
Provides the declarative base for all the custom models
"""

alembic_cfg = Config('alembic.ini')  # Provide the path to your alembic.ini file

type_mapping = {
    "string": String,
    "integer": Integer,
    "number": Float,
    "float": Float,
    "boolean": Boolean,
    "foreign_key": ForeignKey,
    'type': String,
    'core:blueprintattribute': String
}


class Attribute(BaseModel):
    name: str
    type: str
    label: Optional[str] = None
    attributeType: str
    dimensions: Optional[str] = None
    contained: Optional[bool] = None
    optional: Optional[bool] = True


class Blueprint(BaseModel):
    name: str
    type: str
    description: str
    attributes: Optional[List[Attribute]] = None
    path: str = None

    @classmethod
    def from_json(cls, file):
        relative_path = f'{file}.blueprint.json'
        try:
            with open(relative_path, "r") as json_file:
                json_data = json_file.read()
        except FileNotFoundError:
            return None

        blueprint = Blueprint.model_validate_json(json_data)
        blueprint.path = relative_path
        return blueprint

    def generate_models_m2m_rel(self, parent: str = None):
        class_attributes = {}
        children = []
        data_tables = []
        for attr in self.attributes:
            attr_name = attr.name
            if attr_name == 'type':  # no need to store the blueprint type in the database
                continue
            attr_type = attr.attributeType.lower()  # Convert type to lowercase for mapping

            if type_mapping.get(attr_type) and hasattr(attr, 'dimensions') and attr.dimensions == '*':
                # treat this as one-to-many exclusively
                # todo: introduce an integer f_key - auto-generating sequence is not straightforward
                sqlalchemy_data_tale_column_type = type_mapping.get(attr_type)

                if attr.contained:
                    on_delete = 'cascade'
                else:
                    on_delete = None

                data_tables.append({
                    'name': f'{self.name}_{attr_name}',
                    'columns': {
                        f'{self.name}_id': Column(f'{self.name}_id',
                                                  ForeignKey(f'{self.name}.id', ondelete=on_delete),
                                                  primary_key=True, nullable=False, info={"skip_pk": True}),
                        'position': Column(Integer, nullable=False),
                        'data': Column(sqlalchemy_data_tale_column_type, nullable=False),
                        'id': ''
                    }
                })
                class_attributes[attr_name] = relationship(f'{self.name}_{attr_name}',
                                                           order_by=f'{self.name}_{attr_name}.position',
                                                           collection_class=ordering_list('position'))

            elif type_mapping.get(attr_type):  # Should be made to catch any type that is not a blueprint
                sqlalchemy_column_type = type_mapping.get(attr_type)
                class_attributes[attr_name] = Column(sqlalchemy_column_type, nullable=attr.optional)
            else:  # add paths to json-blueprints for children
                file = os.path.normpath(os.path.join(os.path.dirname(self.path), attr_type))
                child_blueprint = self.from_json(file)
                children.append(child_blueprint)
                child_name = child_blueprint.name
                # todo: cascade delete on contained = True
                class_attributes[f'{child_name}_s'] = relationship(child_name,
                                                                   secondary=f'{self.name}_{child_name}_asso',
                                                                   cascade="all,delete")
        if parent:
            table_name = f"{parent}_{self.name}_asso"
            if table_name in globals():
                existing_cols = [c.name for c in globals()[table_name].columns]
                if f"{parent}_id" not in existing_cols or f"{self.name}_id" not in existing_cols:
                    raise ValueError(f'Association table "{table_name}" already exists, but does not correspond to '
                                     f'existing version of "{self.name}"')
            else:
                globals()[table_name] = Table(
                    table_name,
                    Base.metadata,
                    Column(f"{parent}_id",
                           ForeignKey(f"{parent}.id")),
                    Column(f"{self.name}_id",
                           ForeignKey(f"{self.name}.id")),
                )

        if self.name in globals():
            for attr in self.attributes:
                attr_name = attr.name
                if attr_name == 'type':
                    continue
                attr_type = attr.attributeType.lower()
                if type_mapping.get(attr_type):
                    if not getattr(globals()[self.name], attr_name):
                        raise ValueError(f'Attribute "{attr_name}" not found in existing version of "{self.name}"')
        else:
            globals()[self.name] = type(self.name, (Base,), class_attributes)
            for data_table in data_tables:
                globals()[data_table['name']] = type(data_table['name'], (Base,), data_table['columns'])

        for child_blueprint in children:
            child_blueprint.generate_models_m2m_rel(parent=self.name)

    def migrate_and_upgrade(self):
        command.revision(alembic_cfg, autogenerate=True, message=f'table_{self.name}')
        command.upgrade(alembic_cfg, revision='head')

    def return_model(self):
        if self.name in globals():
            return globals()[self.name]
        else:
            return None

    def return_data_table_model(self, name: str):
        if f'{self.name}_{name}' in globals():
            return globals()[f'{self.name}_{name}']
        else:
            return None


class Blueprints(BaseModel):
    bps: List[Blueprint] = []

    def append(self, bp: Blueprint):
        self.bps.append(bp)

    def __len__(self):
        return len(self.bps)

    def __getitem__(self, item):
        return self.bps[item]

    def __iter__(self):
        return iter(self.bps)

    def generate_models(self):
        for blueprint in self.bps:
            blueprint.generate_models_m2m_rel()

    @staticmethod
    def generate_migration_script(message: str = f'models: {datetime.now().strftime("%Y-%m-%d")}'):
        revision = command.revision(alembic_cfg, autogenerate=True, message=message)
        return revision.revision

    @staticmethod
    def upgrade(revision='head'):
        command.upgrade(alembic_cfg, revision=revision)
