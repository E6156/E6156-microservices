from Context.Context import Context
from DataAccess.DataObject import ProfileEntriesRDB as ProfileEntriesRDB
import requests


class ServiceException(Exception):
    unknown_error = 9001
    missing_field = 9002
    bad_data = 9003

    def __init__(self, code=unknown_error, msg="Oh Dear!"):
        self.code = code
        self.msg = msg


class BaseService():
    missing_field = 2001

    def __init__(self):
        pass


class ProfileService(BaseService):
    required_create_fields = ['user_id', 'entry_type', 'entry_subtype', 'entry_value']
    required_update_and_delete_params = ['entry_id']
    required_update_fields = ['entry_type', 'entry_subtype', 'entry_value']

    def __init__(self, ctx=None):
        super().__init__()
        if ctx is None:
            ctx = Context.get_default_context()

        self._ctx = ctx

    @classmethod
    # re-post the address info to address service in order to get a address id
    def check_address(cls, address_entry):
        add_url = Context.get_default_context().get_context("addsvc_url") + "/addresses"
        address_id = None
        if address_entry is not None:
            r_address = requests.post(add_url, json=address_entry)
            if r_address.status_code == 200:
                address_id = r_address.json()['deliver_point_barcode']
        return address_id

    @classmethod
    def get_profile(cls, params):
        result = None
        # simple sanity check
        if params is None or len(params) == 0:
            return result
        required_set = set(cls.required_create_fields)
        required_set.update("profile_id")
        for k in params.keys():
            if k not in required_set:
                return result
        result = ProfileEntriesRDB.get_profile(params, None)
        return result

    @classmethod
    def get_profile_by_user_id(cls, user_id):
        result = ProfileEntriesRDB.get_profile(params={"user_id": user_id}, fields=None)
        return result

    @classmethod
    def delete_profile(cls, user_id, params):
        if user_id is None or params is None:
            return None
        for f in ProfileService.required_update_and_delete_params:
            v = params.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

        params['user_id'] = user_id
        result = ProfileEntriesRDB.delete_profile(params)
        return result

    @classmethod
    def create_profile(cls, profile_info):
        for f in ProfileService.required_create_fields:
            v = profile_info.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)

        if profile_info.get('entry_type', None) == "Address":
            # check address here
            address_id = cls.check_address(profile_info['entry_value'])
            if address_id is None:
                return None
            profile_info['entry_value'] = "address/" + str(address_id)
        return ProfileEntriesRDB.create_profile(profile_info)

    @classmethod
    def update_profile(cls, user_id, profile_info, params):
        if profile_info is None or params is None:
            return None
        for f in ProfileService.required_update_and_delete_params:
            v = params.get(f, None)
            if v is None:
                raise ServiceException(ServiceException.missing_field,
                                       "Missing field = " + f)
        params['user_id'] = user_id

        if profile_info.keys() == ProfileService.required_update_fields:
            raise ServiceException(ServiceException.missing_field,
                                   "Invalid profile entries")

        if profile_info.get('entry_type', None) == "Address":
            # check address here
            address_id = cls.check_address(profile_info['entry_value'])
            if address_id is None:
                return None
            profile_info['entry_value'] = "address/" + str(address_id)
        return ProfileEntriesRDB.update_profile(profile_info, params)
