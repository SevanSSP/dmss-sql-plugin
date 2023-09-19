from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base
import re
from pydantic import BaseModel
from typing import List, Optional
import json
"""
Provides the declarative base for all the custom models
"""


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
        return cls.__name__[0].lower() + re.sub('([A-Z]{1})', r'_\1', cls.__name__[1:]).lower()

    id = Column(Integer, primary_key=True)


# The common source for all future SQLAlchemy classes
Base = declarative_base(cls=ExtendedBaseModel)


class Attribute(BaseModel):
    name: str
    type: str
    label: Optional[str] = None
    attributeType: str
    dimensions: Optional[str] = None
    contained: Optional[bool] = None


class Blueprint(BaseModel):
    name: str
    type: str
    description: str
    attributes: Optional[List[Attribute]] = None


