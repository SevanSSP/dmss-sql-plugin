from plugin.models import Blueprint
import os

blueprint = Blueprint._from_json('models/signals_simple/Case')
blueprint._generate_class()