from Context.Context import Context
from DataAccess.DataObject import UsersRDB as UsersRDB
from uuid import uuid4


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


class ProfileService(BaseService):

    def __init__(self, ctx=None):

        if ctx is None:
            ctx = Context.get_default_context()

        self._ctx = ctx

    @classmethod
    def get_profile(cls, query):

        result = UsersRDB.get_profile(query)
        return result




