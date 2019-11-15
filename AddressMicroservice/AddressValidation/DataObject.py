import AddressValidation.Context as Context
import boto3
import json
import logging

logger = logging.getLogger()

_address_table = None


def _get_address_table(table_name=None, table_region=None):
    global _address_table

    if _address_table is None:
        if table_name is None:
            table_name = Context.get_context()['table_name']
        if table_region is None:
            table_region = Context.get_context()['table_region']
        _address_table = boto3.resource('dynamodb', region_name=table_region).Table(table_name)

    return _address_table


class AddressDynamoDB:
    @classmethod
    def get_address(cls, address_id):
        try:
            table = _get_address_table()
            resp = table.get_item(Key={'deliver_point_barcode': address_id})
            return resp["Item"]
        except Exception as e:
            logger.error("get error: " + str(e))
            return None

    @classmethod
    def post_address(cls, content):
        logger.info('post content ' + json.dumps(content))
        try:
            table = _get_address_table()
            resp = table.put_item(Item=content)
            return resp['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            logger.error("post error: " + str(e))
            return False
