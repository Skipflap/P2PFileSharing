# Encoding and decoding functions + message formats
# protocols.py

import json


def encode_message(**kwargs):
    return json.dumps(kwargs).encode()

def decode_message(data):
    try:
        message = json.loads(data.decode())
        return message
    except json.JSONDecodeError:
        return {}
