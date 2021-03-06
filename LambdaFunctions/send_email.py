import json
import time
import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests

from lambda_utils import *
import jwt.jwt.api_jwt as apij

_secret = "secret"

# Api gateway endpoint to generate redirect link
API_ENDPOINT = os.environ.get("API_ENDPOINT", None)

# Elastic beanstalk endpoint to update user info
EB_ENDPOINT = os.environ.get("EB_ENDPOINT", None)

# S3 endpoint for static webpage
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", None)

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
# SENDER = "Donald F. Ferguson <dff@cs.columbia.edu>"
SENDER = os.environ.get("SENDER", None)

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
RECIPIENT = os.environ.get("RECIPIENT", None)

# Specify a configuration set. If you do not want to use a configuration
# set, comment the following variable, and the
# ConfigurationSetName=CONFIGURATION_SET argument below.
CONFIGURATION_SET = "ConfigSet"

# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
AWS_REGION = "us-east-1"

# The subject line for the email.
SUBJECT = "Email Verification"

# The email body for recipients with non-HTML email clients.
BODY_TEXT = ("Amazon SES Test (Python)\r\n"
             "This email was sent with Amazon SES using the "
             "AWS SDK for Python (Boto)."
             )

# The HTML body of the email.
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Amazon SES Test (SDK for Python)</h1>
  <p>This email was sent with
    <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
    <a href='https://aws.amazon.com/sdk-for-python/'>
      AWS SDK for Python (Boto)</a>.</p>
      <form action="http://google.com">
        <input type="submit" value="Go to Google" />
    </form>
    <p>A really cool verification link would look like: %s
</body>
</html>
            """

# The character encoding for the email.
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client('ses', region_name=AWS_REGION)


# Try to send the email.
def send_email(em, user_id):
    try:
        print("em = ", em, "user_id = ", user_id)
        url = API_ENDPOINT + "?token=" + \
              apij.encode({"time": time.time(), "em": em, "id": user_id}, key=_secret).decode(encoding='UTF-8')
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    em
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML % url,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def handle_sns_event(records):
    sns_event = records[0]['Sns']
    topic_arn = sns_event.get("TopicArn", None)
    topic_subject = sns_event.get("Subject", None)
    topic_msg = sns_event.get("Message", None)

    print("SNS Subject = ", topic_subject)
    if topic_msg:
        json_msg = None
        try:
            json_msg = json.loads(topic_msg)
            print("Message = ", json.dumps(json_msg, indent=2))
        except:
            print("Could not parse message.")

        em = json_msg["email"]
        user_id = json_msg["id"]
        send_email(em, user_id)


def handle_api_event(method, event):
    logger.info("I got an API GW proxy event.")
    logger.info("\nhttpMethod = " + method + "\n")
    redirect_url = S3_ENDPOINT + "/verifail"
    response = respond(None, None, "301", {"Location": redirect_url})
    if method == "GET":
        params = event.get("queryStringParameters", None)
        if params:
            token = params.get("token", None)
            if token:
                token_info = apij.decode(token.encode("utf-8"), key=_secret)
                email = token_info.get("em", None)
                user_id = token_info.get("id", None)
                full_url = EB_ENDPOINT + "/api/user/" + email
                # generate an auth token with role 'admin'
                auth = apij.encode({"msg": "hello from lambda", "time": time.time()}, key=_secret).decode("utf-8")
                # send the ETAG first to avoid race condition
                # get the etag first
                user_get_resp = requests.get(full_url, headers={"Authorization": "Bearer " + auth})
                print('user_get_resp', user_get_resp.status_code)
                if user_get_resp.status_code == 200:
                    # send the ETAG first to avoid race condition
                    user_put_resp = requests.put(full_url, json={"status": "ACTIVE"},
                                                 headers={"ETAG": user_get_resp.headers['ETAG'],
                                                          "Authorization": "Bearer " + auth})
                    print(user_put_resp.status_code)
                    if user_put_resp.status_code == 200:
                        redirect_url = S3_ENDPOINT + "/verisuccess"
                        response = respond(None, None, "301", {"Location": redirect_url})
    return response


def lambda_handler(event, context):
    configure_logging()
    # logger.info("\nEvent = " + json.dumps(event, indent=2) + "\n")

    records = event.get("Records", None)
    method = event.get("httpMethod", None)

    response = respond(None, {"cool": "example"})
    if records:
        handle_sns_event(records)
    elif method:
        response = handle_api_event(method, event)
    else:
        logger.info("Not sure what I got.")

    return response
