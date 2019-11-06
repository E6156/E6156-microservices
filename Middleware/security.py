import jwt
import hashlib
import json
from Context.Context import Context
from time import time

_context = Context.get_default_context()

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
    token_info = {}
    token_info['timestamp'] = str(time())
    email = token_info['email'] = info['email']
    if email == _context.get_context("admin_email"):
        token_info['role']='admin'
    else:
        token_info['role']='student'

    h = jwt.encode(token_info, key=_context.get_context("JWT_SECRET"))
    h = h.decode(encoding='UTF-8')

    return h


# Add different rules to authorize, only check role field
# for now
auth_rules = {
    ("/health", "GET"),
    ("/api/user/<email>", "GET"),
    ("/api/user/<email>", "PUT"),
    ("/api/user/<email>", "DELETE"),
}


def authorize(url, method, token):
    key = (str(url), str(method))
    if key not in auth_rules:
        return True
    try:
        info = jwt.decode(token.split(' ')[1].encode("utf-8"), key=_context.get_context("JWT_SECRET"))
        # lambda can do anything
        msg = info.get('msg', None)
        if msg is not None and msg == 'hello from lambda':
            return True

        role = info.get('role', None)
        if role is None:
            return False
        if key == ("/api/user/<email>", "PUT") \
                or key == ("/api/user/<email>", "DELETE"):
            return role == "admin"
        return role == "admin" or role == "student"
    except Exception as e:
        return False


def calc_hash(data):
    return str(hashlib.md5(json.dumps(data).encode()).hexdigest())
