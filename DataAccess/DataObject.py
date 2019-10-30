import DataAccess.DataAdaptor as data_adaptor
from abc import ABC, abstractmethod
import pymysql.err

class DataException(Exception):

    unknown_error   =   1001
    duplicate_key   =   1002

    def __init__(self, code=unknown_error, msg="Something awful happened."):
        self.code = code
        self.msg = msg

class BaseDataObject(ABC):

    def __init__(self):
        pass

    @classmethod
    @abstractmethod
    def create_instance(cls, data):
        pass


class UsersRDB(BaseDataObject):

    def __init__(self, ctx):
        super().__init__()

        self._ctx = ctx

    @classmethod
    def get_by_email(cls, email):

        sql = "select * from e6156.users where email=%s and status<>%s"
        res, data = data_adaptor.run_q(sql=sql, args=(email, 'DELETED'), fetch=True)
        if data is not None and len(data) > 0:
            result =  data[0]
        else:
            result = None

        return result

    @classmethod
    def get_users(cls, params, fields):

        sql, args = data_adaptor.create_select(table_name="users", template=params, fields=fields)
        res, data = data_adaptor.run_q(sql, args)

        if data is not None and len(data) > 0:
            result = data
        else:
            result = None

        return result

    @classmethod
    def get_login(cls, login_info):

        result = None

        login_fields = {"email","first_name","last_name","password"}
        try:
            sql, args = data_adaptor.create_select(table_name="users", template=login_info, fields=login_fields)
            res, data = data_adaptor.run_q(sql, args)
            if data is not None and len(data) > 0:
                result = data
            else:
                result = None
        except pymysql.err.IntegrityError as ie:
            if ie.args[0] == 1062:
                raise (DataException(DataException.duplicate_key))
            else:
                raise DataException()
        except Exception as e:
            raise DataException()

        return result

    @classmethod
    def create_user(cls, user_info):

        result = None

        try:
            sql, args = data_adaptor.create_insert(table_name="users", row=user_info)
            res, data = data_adaptor.run_q(sql, args)
            if res != 1:
                result = None
            else:
                result = user_info['id']
        except pymysql.err.IntegrityError as ie:
            if ie.args[0] == 1062:
                raise (DataException(DataException.duplicate_key))
            else:
                raise DataException()
        except Exception as e:
            raise DataException()

        return result

    @classmethod
    def delete_user(cls, email):
        result = None
        user_info = UsersRDB.get_by_email(email)
        if user_info is None:
            return result
        try:
            sql, args = data_adaptor.create_update(table_name="users",
                                                   new_values={"status": "DELETED"},
                                                   template={"email": email})
            res, data = data_adaptor.run_q(sql, args)
            if res != 1:
                result = None
            else:
                result = user_info['id']

        except Exception as e:
            raise DataException()

        return result

    @classmethod
    def update_user(cls, email, data):
        result = None
        user_info = UsersRDB.get_by_email(email)
        if user_info is None:
            return result
        try:
            sql, args = data_adaptor.create_update(table_name="users",
                                                   new_values=data,
                                                   template={"email": email})
            res, data = data_adaptor.run_q(sql, args)
            if res != 1:
                result = None
            else:
                result = user_info['id']

        except Exception as e:
            raise DataException()

        return result



