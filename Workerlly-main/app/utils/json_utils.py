from bson import ObjectId
from bson.json_util import default, CANONICAL_JSON_OPTIONS


def custom_json_encoder(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return default(obj, json_options=CANONICAL_JSON_OPTIONS)
