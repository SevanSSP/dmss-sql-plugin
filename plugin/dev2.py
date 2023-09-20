from plugin.models import Blueprint

blueprint = Blueprint._from_json('models/signals_simple/Case')
blueprint._generate_class()