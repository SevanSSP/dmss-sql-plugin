from uuid import uuid4
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import re
from pydantic import BaseModel
from typing import List, Optional
from alembic.config import Config
from alembic import command
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, text
import os

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


class ExtendedBaseModel(object):
    """
    Base for all database models.
    """

    @declared_attr
    def __tablename__(cls):
        """
        Sets the SQL table name to a lower case version of the class name where capital
        letter are replaced by underscore and the lower case letter. The underscore is
        not added to the first letter. Example: AnExampleThing will be given
        __tablename__ = 'an_example_thing'
        """
        return cls.__name__.lower()

    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True, nullable=False,
                server_default=text("uuid_generate_v4()"))


# The common source for all future SQLAlchemy classes
Base = declarative_base(cls=ExtendedBaseModel)


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
    def _from_json(cls, file):
        relative_path = f'{file}.blueprint.json'
        with open(relative_path, "r") as json_file:
            json_data = json_file.read()
        blueprint = Blueprint.model_validate_json(json_data)
        blueprint.path = relative_path
        return blueprint

    def _generate_class(self, parent: str = None):
        class_attributes = {}
        children = []
        for attr in self.attributes:
            attr_name = attr.name
            attr_type = attr.attributeType.lower()  # Convert type to lowercase for mapping

            if type_mapping.get(attr_type): #Should be made to catch any type that is not a blueprint
                sqlalchemy_column_type = type_mapping.get(attr_type)
                class_attributes[attr_name] = Column(sqlalchemy_column_type, nullable=attr.optional)
            else: #add paths to json-blueprints for children
                file = os.path.normpath(os.path.join(os.path.dirname(self.path), attr_type))
                children.append(file)
                child_table = attr_type.split('/')[-1]
                class_attributes[child_table] = relationship(child_table, backref=self.name, cascade="all,delete")

        if parent: #Add fk-relation to parent by using parent blueprint_id
            class_attributes[f'{parent.lower()}_id'] = Column(UUID(as_uuid=True), ForeignKey(f'{parent.lower()}.id', ondelete="cascade"), nullable=False)

        base_class = Base
        globals()[self.name] = type(self.name, (base_class,), class_attributes)
        revision_id = command.revision(alembic_cfg, autogenerate=True, message=f"table_{self.name}")
        command.upgrade(alembic_cfg, "head")
        for i in children:
            child_blueprint = self._from_json(i)
            child_blueprint._generate_class(parent=self.name)
