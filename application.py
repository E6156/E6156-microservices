
# Import functions and objects the microservice needs.
# - Flask is the top-level application. You implement the application by adding methods to it.
# - Response enables creating well-formed HTTP/REST responses.
# - requests enables accessing the elements of an incoming HTTP/REST request.
#
from flask import Flask, Response, redirect, url_for
from flask_cors import CORS

from datetime import datetime
import json

from Services.CustomerProfile.Profile import ProfileService as ProfileService
from Services.CustomerInfo.Users import UsersService as UserService
from Services.RegisterLogin.RegisterLogin import RegisterLoginSvc as RegisterLoginSvc
from Context.Context import Context
from Middleware.notification import publish_it
import Middleware.security as middleware_security
import Middleware.notification as middleware_notification
from functools import wraps
from flask import g, request, redirect, url_for
import jwt

# Setup and use the simple, common Python logging framework. Send log messages to the console.
# The application should get the log level out of the context. We will change later.
#
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not middleware_security.authorize(request.url_rule, request.method,
                                             request.headers.get("Authorization", None)):
            return Response("Please login first", status=403, content_type="text/plain")
        return f(*args, **kwargs)
    return decorated_function

###################################################################################################################
#
# AWS put most of this in the default application template.
#
# AWS puts this function in the default started application
# print a nice greeting.
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

# AWS put this here.
# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>EB Flask Test</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Thelonious</code>) to say hello to
    someone specific.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

# EB looks for an 'application' callable by default.
# This is the top-level application that receives and routes requests.
application = Flask(__name__)
CORS(application)

# add a rule for the index page. (Put here by AWS in the sample)
application.add_url_rule('/', 'index', (lambda: header_text +
    say_hello() + instructions + footer_text))

# add a rule when the page is accessed with a name appended to the site
# URL. Put here by AWS in the sample
application.add_url_rule('/<username>', 'hello', (lambda username:
    header_text + say_hello(username) + home_link + footer_text))

##################################################################################################################
# The stuff I added begins here.

_default_context = None
_user_service = None
_profile_service = None
_registration_service = None

@application.after_request
def after_decorator(rsp):
    return rsp

def do_something_after(rsp):

    #only an admin can delete
    if request.method == 'DELETE':
        token = request.headers.get("Authorization", None)
        info = jwt.decode(token.split(' ')[1].encode("utf-8"),
                          key=Context.get_default_context().get_context("JWT_SECRET"))
        role = info.get('role', None)
        if role != 'admin':
            rsp = Response("Not authorized", status=403, content_type="text/plain")
    #a customer can update
    if request.method == 'PUT':
        token = request.headers.get("Authorization", None)
        info = jwt.decode(token.split(' ')[1].encode("utf-8"),
                          key=Context.get_default_context().get_context("JWT_SECRET"))
        role = info.get('role', None)
        if role != 'student':
            rsp = Response("Not authorized", status=403, content_type="text/plain")
    return rsp

def _get_default_context():

    global _default_context

    if _default_context is None:
        _default_context = Context.get_default_context()

    return _default_context

def _get_user_service():
    global _user_service

    if _user_service is None:
        _user_service = UserService(_get_default_context())

    return _user_service

def _get_profile_service():
    global _profile_service

    if _profile_service is None:
        _profile_service = ProfileService(_get_default_context())

    return _profile_service

def _get_registration_service():
    global _registration_service

    if _registration_service is None:
        _registration_service = RegisterLoginSvc()

    return _registration_service

def linked_data_assembler(uid):
    href_string = "/api/customers/" + str(uid) + "/profile"
    profile_link_frame = {
        "rel" : "profile",
        "href" : href_string,
        "method" : "GET"
    }

    return profile_link_frame

def init():

    global _default_context, _user_service

    _default_context = Context.get_default_context()
    _user_service = UserService(_default_context)
    _registration_service = RegisterLoginSvc()

    logger.debug("_user_service = " + str(_user_service))

# 1. Extract the input information from the requests object.
# 2. Log the information
# 3. Return extracted information.
#
def log_and_extract_input(method, path_params=None):

    path = request.path
    args = dict(request.args)
    data = None
    headers = dict(request.headers)
    method = request.method

    try:
        if request.data is not None:
            data = request.json
        else:
            data = None
    except Exception as e:
        # This would fail the request in a more real solution.
        data = "You sent something but I could not get JSON out of it."

    log_message = str(datetime.now()) + ": Method " + method

    inputs =  {
        "path": path,
        "method": method,
        "path_params": path_params,
        "query_params": args,
        "headers": headers,
        "body": data
        }

    log_message += " received: \n" + json.dumps(inputs, indent=2)
    logger.debug(log_message)

    return inputs

def log_response(method, status, data, txt):

    msg = {
        "method": method,
        "status": status,
        "txt": txt,
        "data": data
    }

    logger.debug(str(datetime.now()) + ": \n" + json.dumps(msg, indent=2))

# This function performs a basic health check. We will flesh this out.
@application.route("/health", methods=["GET"])
@login_required
def health_check():

    rsp_data = { "status": "healthy", "time": str(datetime.now()) }
    rsp_str = json.dumps(rsp_data)
    rsp = Response(rsp_str, status=200, content_type="application/json")
    return rsp

@application.route("/demo/<parameter>", methods=["GET", "POST"])
def demo(parameter):

    inputs = log_and_extract_input(demo, { "parameter": parameter })

    msg = {
        "/demo received the following inputs" : inputs
    }

    rsp = Response(json.dumps(msg), status=200, content_type="application/json")
    return rsp

@application.route("/api/users", methods=["GET"])
@login_required
def users():

    global _user_service

    inputs = log_and_extract_input(users)
    rsp_data = None

    try:

        user_service = _get_user_service()

        logger.error("/users: _user_service = " + str(user_service))

        if inputs["method"] == "GET":

            query_params = inputs["query_params"]

            if "fields" not in inputs["query_params"]:
                fields = None
            else:
                fields = inputs["query_params"].pop("fields").split(",")

            rsp = user_service.get_users(query_params, fields)

            if rsp is not None:
                rsp_data = rsp
                rsp_status = 200
                rsp_txt = "OK"

        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/users: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/users", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/user/<email>", methods=["GET", "PUT", "DELETE"])
@login_required
def user_email(email):
    global _user_service

    inputs = log_and_extract_input(demo, { "parameters": email })
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:
        etag = None
        user_service = _get_user_service()

        logger.error("/email: _user_service = " + str(user_service))

        if inputs["method"] == "GET":

            rsp, etag = user_service.get_by_email(email)

            if rsp is not None:
                rsp_data = rsp
                rsp_data["links"] = linked_data_assembler(rsp["id"])
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NOT FOUND"

        elif inputs["method"] == "PUT":
            rsp_id, etag = user_service.update_user(email, inputs["body"], inputs["headers"].get("Etag", None))
            if rsp_id is not None:
                rsp_status = 200
                rsp_txt = "id = " + rsp_id + " user updated."
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "can not update"

        elif request.method == 'DELETE':
            rsp_id, etag = user_service.delete_user(email, inputs["headers"].get("Etag", None))
            if rsp_id is not None:
                rsp_status = 200
                rsp_txt = "id = " + rsp_id + " user deleted."
                rsp_data = rsp_id
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NOT FOUND"

        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

        if etag is not None:
            full_rsp.headers["ETAG"] = etag

    except Exception as e:
        log_msg = "/email: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/email", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/profile", methods=["GET", "POST"])
# @login_required
def profile():
    global _profile_service
    global _user_service

    inputs = log_and_extract_input(demo)
    logger.error("/profile: input = " + str(inputs))
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:
        profile_service = _get_profile_service()

        logger.error("/profile: _profile_service = " + str(profile_service))

        if inputs["method"] == "GET":
            full_rsp = profile_service.get_profile(inputs["query_params"])

            if full_rsp is not None:
                rsp_data = full_rsp
                rsp_status = 201
                rsp_txt = "Profile retrieved."
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "Cannot get profile."

        elif inputs["method"] == "POST":
            full_rsp = profile_service.create_profile(inputs["body"])

            if full_rsp is not None:
                rsp_status = 201
                rsp_txt = "Profile " + full_rsp + " created."
            else:
                rsp_data = None
                rsp_status = 400
                rsp_txt = "Cannot create profile."

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/profile: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Customer profile creation cannot be processed."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/profile", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/customers/<customer_id>/profile", methods=["GET"])
# @login_required
def customers_profile(customer_id):
    return redirect(url_for('profile', user_id=customer_id))

@application.route("/api/profile/<customer_id>", methods=["GET", "PUT", "DELETE"])
# @login_required
def profile_customer_id(customer_id):
    global _profile_service
    global _user_service

    inputs = log_and_extract_input(demo, { "parameters": customer_id })
    logger.error("/profile: input = " + str(inputs))
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:
        profile_service = _get_profile_service()

        logger.error("/profile: _profile_service = " + str(profile_service))

        if inputs["method"] == "GET":
            full_rsp = profile_service.get_profile_by_user_id(customer_id)

            if full_rsp is not None:
                rsp_data = full_rsp
                rsp_status = 200
                rsp_txt = "OK"
            else:
                rsp_status = 404
                rsp_txt = "NOT FOUND"

        elif inputs["method"] == "PUT":
            rsp_id = profile_service.update_profile(customer_id, inputs["body"], inputs["query_params"])

            if rsp_id is not None:
                rsp_status = 200
                rsp_txt = "id = " + rsp_id + " profile updated."
            else:
                rsp_status = 404
                rsp_txt = "can not update"

        elif request.method == 'DELETE':
            rsp_id = profile_service.delete_profile(customer_id, inputs["query_params"])

            if rsp_id is not None:
                rsp_status = 200
                rsp_txt = "id = " + rsp_id + " user deleted."
            else:
                rsp_status = 404
                rsp_txt = "NOT FOUND"

        if rsp_data is not None:
            full_rsp = Response(json.dumps(rsp_data), status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/profile: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Customer profile cannot be processed."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/profile", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/registration", methods=["POST"])
def registration():

    inputs = log_and_extract_input(demo, {"parameters": None})
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:

        r_svc = _get_registration_service()

        logger.error("/api/registration: _r_svc = " + str(r_svc))
        link = None
        auth = None
        user_id = None
        if inputs["method"] == "POST":

            rsp = r_svc.register(inputs['body'])

            if rsp is not None:
                rsp_data = rsp
                rsp_status = 201
                rsp_txt = "CREATED"
                link = rsp_data[0]
                auth = rsp_data[1]
                user_id = rsp_data[2]
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = "NOT FOUND"
        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            # TODO Generalize generating links
            headers = {"Location": "/api/users/" + link}
            # Workaround to make authorization seen by Angular frontend
            headers["Access-Control-Expose-Headers"] = "Authorization"
            headers["Authorization"] = "Bearer " + auth
            # Send the email and id to lambda in order to generate the query string with ETAG
            publish_it({"email": link, "id": user_id})
            full_rsp = Response(rsp_txt, headers=headers,
                                status=rsp_status, content_type="text/plain")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/api/registration: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/registration", rsp_status, rsp_data, rsp_txt)

    return full_rsp

@application.route("/api/login", methods=["POST"])
def login():

    inputs = log_and_extract_input(demo, {"parameters": None})
    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:
        rsp = None
        r_svc = _get_registration_service()

        logger.error("/api/login: _r_svc = " + str(r_svc))

        if inputs["method"] == "POST":

            rsp = r_svc.login(inputs['body'])

            if rsp is not None and rsp is not False:
                rsp_data = "OK"
                rsp_status = 201
                rsp_txt = "CREATED"
            else:
                rsp_data = None
                rsp_status = 403
                rsp_txt = "NOT AUTHORIZED"
        else:
            rsp_data = None
            rsp_status = 501
            rsp_txt = "NOT IMPLEMENTED"

        if rsp_data is not None:
            # TODO Generalize generating links
            headers = {"Authorization": "Bearer " + rsp[0]}
            headers["Access-Control-Expose-Headers"] = "Authorization"
            headers["Location"] = "/api/users/" + rsp[1]
            full_rsp = Response(json.dumps(rsp_data, default=str), headers=headers,
                                status=rsp_status, content_type="application/json")
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    except Exception as e:
        log_msg = "/api/login: Exception = " + str(e)
        logger.error(log_msg)
        rsp_status = 500
        rsp_txt = "INTERNAL SERVER ERROR. Please take COMSE6156 -- Cloud Native Applications."
        full_rsp = Response(rsp_txt, status=rsp_status, content_type="text/plain")

    log_response("/api/login", rsp_status, rsp_data, rsp_txt)

    return full_rsp

logger.debug("__name__ = " + str(__name__))
# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.

    logger.debug("Starting Project EB at time: " + str(datetime.now()))
    init()

    application.debug = True
    application.after_request(do_something_after)
    application.run()