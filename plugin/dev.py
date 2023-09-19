from plugin.models import Blueprint, Attribute, ExtendedBaseModel, Base
from alembic import autogenerate
from alembic.config import Config
from alembic import command
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey

# Mapping between Pydantic attribute types and SQLAlchemy column types
type_mapping = {
    "string": String,
    "integer": Integer,
    "float": Float,
    "boolean": Boolean,
    "foreign_key": ForeignKey,
}

alembic_cfg = Config("alembic.ini")  # Provide the path to your alembic.ini file

json_file_path = 'blueprints/study.json'

with open(json_file_path, "r") as json_file:
    json_data = json_file.read()

blueprint_study = Blueprint.model_validate_json(json_data)

json_file_path = 'blueprints/case.json'

with open(json_file_path, "r") as json_file:
    json_data = json_file.read()

blueprint_case = Blueprint.model_validate_json(json_data)


def _generate_class(blueprint):
    class_attributes = {}
    for attr in blueprint.attributes:
        attr_name = attr.name
        attr_type = attr.type.lower()  # Convert type to lowercase for mapping
        sqlalchemy_column_type = type_mapping.get(attr_type, String)  # Default to String if type not found
        class_attributes[attr_name] = Column(sqlalchemy_column_type)

    base_class = Base
    globals()[blueprint.name] = type(blueprint.name, (base_class,), class_attributes)
    revision_id = command.revision(alembic_cfg, autogenerate=True, message=f"table_{blueprint.name}")
    command.upgrade(alembic_cfg, "head")



_generate_class(blueprint_case)
