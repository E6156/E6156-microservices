import jwt
from Context.Context import Context
from time import time

_context = Context()

def hash_password(pwd):
    global _context
    h = jwt.encode(pwd , key=_context.get_context("JWT_SECRET"))
    return h


def generate_token_old(email):

    token = {
        "email": email,
        "timestamp": time()
    }

    if uni == 'dff9':
        token['role']='admin'
    else:
        token['role']='student'

    h = jwt.encode(token, key=_context.get_context("JWT_SECRET"))

    return h

def generate_token(info):

    info["timestamp"] =  time()
    email = info['email']

    if email == 'dff9@columbia.edu':
        info['role']='admin'
    else:
        info['role']='student'

    info['created'] = str(info['created'])

    h = jwt.encode(info, key=_context.get_context("JWT_SECRET"))
    h = str(h)

    return h