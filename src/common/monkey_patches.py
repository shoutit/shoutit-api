import uuid
from json import JSONEncoder
default_json_encoder_default = JSONEncoder().default  # save the JSONEncoder default function


# Monkey Patching all the JSON imports
class ShoutitCustomJSONEncoder(JSONEncoder):
    def default(self, obj):

        # case: UUID
        if isinstance(obj, uuid.UUID):
            return str(obj)

        # case: Class
        # if isinstance(obj, Class):
        #     return class_to_str(obj)

        # default:
        return default_json_encoder_default(obj)  # call the saved default function

JSONEncoder.default = ShoutitCustomJSONEncoder().default  # replace the JSONEncoder default function with custom one
