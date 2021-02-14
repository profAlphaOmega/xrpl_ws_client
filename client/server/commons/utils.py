import uuid
import time
import json
from flask import jsonify

from server.logger import logger

def generate_uuid(string=''):
    if not string:
        string = str(int(time.time()))
    if not type(string) is str:
        string = json.dumps(string)
    return uuid.uuid5(uuid.NAMESPACE_OID, string).hex


def make_resp(msg, status_code):
    """builds the return response in json format"""
    response = jsonify(message=msg)
    response.status_code = status_code
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Content-Type'] = '*'
    return response
