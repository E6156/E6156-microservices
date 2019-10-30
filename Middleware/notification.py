import boto3
import json
import os


def publish_it(msg):
    topic_arn = os.environ['topic_arn']
    client = boto3.client('sns', region_name='us-east-2')
    txt_msg = json.dumps(msg)

    client.publish(TopicArn=topic_arn,
                   Message=txt_msg)