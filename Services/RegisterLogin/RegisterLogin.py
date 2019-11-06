import Middleware.security as security
from Context.Context import Context
from Services.CustomerInfo.Users import UsersService as user_svc

class RegisterLoginSvc():

    _context = None

    @classmethod
    def set_context(cls, ctx):
        RegisterLoginSvc._context = ctx

    @classmethod
    def get_data_object(cls):
        return None

    @classmethod
    def get_context(cls):
        if cls._context is None:
            cls.set_context(Context.get_default_context())
        return cls._context

    @classmethod
    def register(cls, data):
        hashed_pw = security.hash_password({"password" : data['password']})
        data["password"] = str(hashed_pw)
        user_id = user_svc.create_user(data)
        if user_id:
            tok = security.generate_token(data)
            return data['email'], tok, user_id
        else:
            return None

    @classmethod
    def login(cls, login_info):
        try:
            test = security.hash_password({"password": login_info['password']})
            s_info, _ = user_svc.get_by_email(login_info['email'])
            test = str(test)
            if str(test) == s_info['password']:
                tok = security.generate_token(s_info)
                return tok, login_info['email']
            else:
                return False
        except Exception as e:
            return False
