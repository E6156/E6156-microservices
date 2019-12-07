import DataAccess.DataAdaptor as data_adaptor
from abc import ABC, abstractmethod
import pymysql.err
import Middleware.security as middleware_security
from uuid import uuid4

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

class ProfileEntriesRDB(BaseDataObject):

    @classmethod
    def get_profile(cls, params, fields):

        sql, args = data_adaptor.create_select(table_name="profile_entries", template=params, fields=fields)
        res, data = data_adaptor.run_q(sql, args)

        if data is not None and len(data) > 0:
            result = data
        else:
            result = None

        return result

    @classmethod
    def create_profile(cls, profile_info):
        result = None
        conn = None
        cursor = None

        try:
            conn = data_adaptor._get_default_connection()
            cursor = conn.cursor()

            # a wrapper function helps to pass params
            def run_q(sql_, args_):
                return data_adaptor.run_q(sql_, args_, cur=cursor, conn=conn, commit=False)

            # confirm the profile id first
            sql = "select distinct profile_id from e6156.profile_entries where user_id=%s"
            res, data = run_q(sql, (profile_info['user_id']))
            if data is not None and len(data) > 0:
                profile_info['profile_id'] = data[0]['profile_id']
            else:
                profile_info['profile_id'] = str(uuid4())

            # post the profile info
            sql, args = data_adaptor.create_insert(table_name="profile_entries", row=profile_info)

            res, _ = run_q(sql, args)
            if res != 1:
                raise Exception('cannot post data!')

            # commit the successful transaction
            conn.commit()
            result = profile_info['user_id']
        except Exception as e:
            # rollback if anything bad happens
            conn.rollback()
        finally:
            # closing database connection.
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            return result

    @classmethod
    def delete_profile(cls, params):
        result = None
        sql, args = data_adaptor.create_delete(table_name="profile_entries",
                                               template=params)
        res, _ = data_adaptor.run_q(sql=sql, args=args)
        if res == 1:
            result = params['user_id']
        return result

    @classmethod
    def update_profile(cls, profile_info, params):
        result = None
        sql, args = data_adaptor.create_update(table_name="profile_entries",
                                               new_values=profile_info,
                                               template=params)
        res, _ = data_adaptor.run_q(sql=sql, args=args)
        if res == 1:
            result = params['user_id']
        return result


class UsersRDB(BaseDataObject):

    def __init__(self, ctx):
        super().__init__()

        self._ctx = ctx

    @classmethod
    def get_by_email(cls, email):
        # Only get the user not deleted
        sql = "select * from e6156.users where email=%s and status<>%s"
        res, data = data_adaptor.run_q(sql=sql, args=(email, 'DELETED'), fetch=True)
        if data is not None and len(data) > 0:
            result = data[0]
        else:
            result = None

        return result, middleware_security.calc_hash(result)

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
            if res == 1:
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
    def update_user(cls, email, data, etag):
        result = None, None
        conn = None
        cursor = None
        try:
            conn = data_adaptor._get_default_connection()
            cursor = conn.cursor()

            # a wrapper function helps to pass params
            def run_q(sql_, args_):
                return data_adaptor.run_q(sql_, args_, cur=cursor, conn=conn, commit=False)

            sql, args = data_adaptor.create_select(table_name="users", template={"email": email})

            _, prev_data = run_q(sql, args)

            if prev_data is not None and len(prev_data) > 0:
                prev_etag = middleware_security.calc_hash(prev_data[0])
                if prev_etag != etag:
                    raise Exception('outdated Etag!')
                sql, args = data_adaptor.create_update(table_name="users",
                                                       new_values=data,
                                                       template={"email": email})
                res, _ = run_q(sql, args)
                if res != 1:
                    raise Exception('cannot update data!')
                else:
                    # calc new etag based on updated data
                    new_data = prev_data[0]
                    for k, v in data.items():
                        new_data[k] = v
                    result = new_data['id'], middleware_security.calc_hash(new_data)
                # commit the successful transaction
                conn.commit()
            else:
                raise Exception('cannot retrieve data')

        except Exception as e:
            # rollback if anything bad happens
            conn.rollback()
        finally:
            # closing database connection.
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            return result


