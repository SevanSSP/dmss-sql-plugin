from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Optional
from alembic.config import Config
from alembic import command
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
import os
from datetime import datetime
import re

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
        with open(relative_path, "r") as json_file:
            json_data = json_file.read()
        blueprint = Blueprint.model_validate_json(json_data)
        blueprint.path = relative_path
        return blueprint

    def generate_models_m2m_rel(self, parent: str = None):
        class_attributes = {}
        children = []
        for attr in self.attributes:
            attr_name = attr.name
            attr_type = attr.attributeType.lower()  # Convert type to lowercase for mapping

            if type_mapping.get(attr_type):  # Should be made to catch any type that is not a blueprint
                sqlalchemy_column_type = type_mapping.get(attr_type)
                class_attributes[attr_name] = Column(sqlalchemy_column_type, nullable=attr.optional)
            else:  # add paths to json-blueprints for children
                file = os.path.normpath(os.path.join(os.path.dirname(self.path), attr_type))
                children.append(file)
                child_table = attr_type.split('/')[-1]
                class_attributes[f'{child_table}_s'] = relationship(child_table,
                                                                    secondary=f'{self.name}_{child_table}_asso',
                                                                    cascade="all,delete")
        if parent:
            table_name = f"{parent}_{self.name}_asso"
            if table_name in globals():
                existing_cols = [c.name for c in globals()[table_name].columns]
                if f"{parent}_id" not in existing_cols or f"{self.name}_id" not in existing_cols:
                    raise ValueError(f'Association table "{table_name}" already exists, but does not correspond to '
                                     f'existing version of "{self.name}"')
            else:
                # todo: cascade delete on contained = True
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
                attr_type = attr.attributeType.lower()
                if type_mapping.get(attr_type):
                    if not getattr(globals()[self.name], attr_name):
                        raise ValueError(f'Attribute "{attr_name}" not found in existing version of "{self.name}"')
        else:
            base_class = Base
            globals()[self.name] = type(self.name, (base_class,), class_attributes)

        for i in children:
            child_blueprint = self.from_json(i)
            child_blueprint.generate_models_m2m_rel(parent=self.name)

    def migrate_and_upgrade(self):
        command.revision(alembic_cfg, autogenerate=True, message=f'table_{self.name}')
        command.upgrade(alembic_cfg, revision='head')


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
        return command.revision(alembic_cfg, autogenerate=True, message=message)

    @staticmethod
    def upgrade(revision='head'):
        command.upgrade(alembic_cfg, revision=revision)
