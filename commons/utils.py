import uuid
import time
import json


def generate_uuid(seed=''):
    if not seed:
        seed = str(int(time.time()))
    if not type(seed) is str:
        seed = json.dumps(seed)
    return uuid.uuid5(uuid.NAMESPACE_OID, seed).hex


