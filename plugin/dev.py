from plugin.models import Blueprint, Attribute, ExtendedBaseModel

json_file_path = 'plugin/study.json'

with open(json_file_path, "r") as json_file:
    json_data = json_file.read()

blueprint_study = Blueprint.model_validate_json(json_data)

json_file_path = 'plugin/case.json'

with open(json_file_path, "r") as json_file:
    json_data = json_file.read()

blueprint_case = Blueprint.model_validate_json(json_data)

def _generate_class(blueprint):
    class_attributes = {attr.name: attr.attributeType for attr in blueprint.attributes}
    globals()[blueprint.name] = type(blueprint.name, (ExtendedBaseModel,), class_attributes)
