
@classmethod
def login(cls, login_info):
    test = security.hash_password({"password": login_info['password']})
    s_info = student_svc.get_by_uni(login_info['email'])
    if test == s_info:
        return True
    else:
        return False