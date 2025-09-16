import json

from bson import ObjectId


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


def convert_objectid_to_str(doc):
    """
    Recursively convert ObjectId to string in a document
    """
    if not isinstance(doc, dict):
        return doc

    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, dict):
            doc[k] = convert_objectid_to_str(v)
        elif isinstance(v, list):
            doc[k] = [
                convert_objectid_to_str(item) if isinstance(item, dict) else item
                for item in v
            ]
    return doc
