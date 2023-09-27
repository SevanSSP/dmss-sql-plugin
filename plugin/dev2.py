# from plugin.models import Blueprint
#
# blueprint = Blueprint.from_json('models/signals_simple/Case')
# blueprint.generate_class_m2m_rel()
#
# blueprint = Blueprint.from_json('models/signals_simple/StudyNC')
# blueprint.generate_class_m2m_rel()
#
# blueprint = Blueprint.from_json('models/signals_simple/Study')
# blueprint.generate_class_m2m_rel()

from plugin.models import initialize_database
import os

base_folder = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', "models"))
initialize_database(base_folder=base_folder)
