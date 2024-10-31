# Encoding and decoding functions + message formats
# protocols.py

def encode_message(**kwargs):
    return str(kwargs).encode()


def decode_message(data):
    try:
        message = eval(data.decode())
        return message
    except:
        return {}
    
    