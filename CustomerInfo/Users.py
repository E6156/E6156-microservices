from abc import ABC, abstractmethod
from Context.Context import Context
from DataAccess.DataObject import UsersRDB as UsersRDB
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash


# The base classes would not be IN the project. They would be in a separate included package.
# They would also do some things.

class ServiceException(Exception):

    unknown_error   =   9001
    missing_field   =   9002
    bad_data        =   9003

    def __init__(self, code=unknown_error, msg="Oh Dear!"):
        self.code = code
        self.msg = msg


class BaseService():

    missing_field   =   2001

    def __init__(self):
        pass


class UsersService(BaseService):

    required_create_fields = ['last_name', 'first_name', 'email', 'password']

    def __init__(self, ctx=None):

        if ctx is None:
            ctx = Context.get_default_context()

        self._ctx = ctx

    @classmethod
    def hash_password(cls, user_info):

        hashed_pwd = ''

        for f in UsersService.required_create_fields:
            v = user_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            if f == 'password':
               hashed_pwd = generate_password_hash(v)

        user_info['password'] = hashed_pwd

        return user_info

    def check_hash_password(cls, user_info, user_info_db):

        hashed_pwd_check = False

        for f in UsersService.required_create_fields:
            v = user_info.get(f, None)
            v_db = user_info_db.get(f, None)
            if v_db is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            if f == 'password':
               hashed_pwd_check = check_password_hash(v_db, user_info['password'])

        return hashed_pwd_check

    @classmethod
    def get_by_email(cls, email):

        result = UsersRDB.get_by_email(email)
        return result

    @classmethod
    def get_users(cls, params, fields):

        result = UsersRDB.get_users(params, fields)
        return result

    @classmethod
    def get_login(cls, email):

        result = UsersRDB.get_login(email)
        return result

    @classmethod
    def create_user(cls, user_info):



        for f in UsersService.required_create_fields:
            v = user_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            if f == 'email':
                if v.find('@') == -1:
                    raise ServiceException(ServiceException.bad_data,
                           "Email looks invalid: " + v)

        user_info['id'] = str(uuid4())
        user_info['status'] = 'PENDING'
        result = UsersRDB.create_user(user_info=user_info)

        return result

    @classmethod
    def delete_user(cls, email):
        if email.find('@') == -1:
            raise ServiceException(ServiceException.bad_data,
                                   "Email looks invalid: " + email)

        return UsersRDB.delete_user(email=email)

    @classmethod
    def update_user(cls, email, data):
        if email.find('@') == -1:
            raise ServiceException(ServiceException.bad_data,
                                   "Email looks invalid: " + email)
        for k in data:
            if k != "status" and k not in set(UsersService.required_create_fields):
                raise ServiceException(ServiceException.bad_data,
                                       "Invalid field: " + k)
        return UsersRDB.update_user(email=email, data=data)


