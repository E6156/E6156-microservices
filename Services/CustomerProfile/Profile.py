from Context.Context import Context
from DataAccess.DataObject import ProfileEntriesRDB as ProfileEntriesRDB
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

    required_create_fields = ['entry_type', 'entry_subtype', 'entry_value']

    def __init__(self, ctx=None):

        if ctx is None:
            ctx = Context.get_default_context()

        self._ctx = ctx

    @classmethod
    def get_profile(cls, query):

        result = ProfileEntriesRDB.get_profile(query)
        return result


    @classmethod
    def get_user_profile(cls, param_value):

        result = ProfileEntriesRDB.get_profile_query(param_value)
        return result

    @classmethod
    def delete_profile(cls, param_value):

        result = ProfileEntriesRDB.delete_profile(param_value)
        return result

    @classmethod
    def update_profile(cls, profile_id, data, address_id):
        template = {}
        update_data_dict = {}
        update_data = ""
        for f in ProfileService.required_create_fields:
            v = data.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            if f == 'entry_value':
                update_data = "entry_value="+ "'" +str(data.get(f, None))+"'"
                update_data_dict['entry_value'] = data.get(f, None)
            if f == 'entry_type':
                template['entry_type'] = data.get(f, None)
            if f == 'entry_subtype':
                template['entry_subtype'] = data.get(f, None)

        if template['entry_type'] == 'Address':
            update_data_dict['entry_value'] = address_id

        template['user_id'] = profile_id

        return ProfileEntriesRDB.update_profile(param_profile=profile_id, update_template=template, data=update_data_dict)

    @classmethod
    def create_profile_entry(cls, param_value, profile_info, address_id):
        for f in ProfileService.required_create_fields:
            v = profile_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            elif f == 'entry_type':
                if profile_info.get(f, None) == "Address":
                    profile_info['entry_value']=address_id

        profile_info['user_id'] = param_value
        profile_info['profile_entry_id'] = str(uuid4())
        result = ProfileEntriesRDB.create_profile_entry(profile_info)
        if result:
            return result
        else:
            return None

    @classmethod
    def retrieve_address(cls, param_value, profile_info):

        isAddress = False
        for f in ProfileService.required_create_fields:
            v = profile_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

            elif f == 'entry_type':
                if profile_info.get(f, None) == "Address":
                    isAddress = True
            elif f == 'entry_value':
                if isAddress == True:
                    result = v

        if result:
            return result
        else:
            return None